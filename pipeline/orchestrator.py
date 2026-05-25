"""
orchestrator.py
===============
The top-level pipeline that chains everything together:

    Image -> Segmentation -> Tissue Classification -> Healing Prediction

Usage:
    from pipeline.orchestrator import DFUPipeline
    pipe = DFUPipeline()
    result = pipe.run("data/sample_inputs/woundtst.jpg", case_id="CASE_001")

The DFUPipeline class loads all three models once (which is slow),
then each call to run() is quick. If you're only processing one image,
the convenience function run_pipeline() at the bottom also works
(but it reloads models every call — prefer the class for any real use).

DISCLAIMER: This is a research prototype. The healing prediction is based
on simulated wound progression, not real multi-visit data. Do not use
this system for clinical decision-making.
"""

import logging
import warnings
import numpy as np

from pipeline.config import ensure_output_dirs, LOG_FORMAT, LOG_LEVEL
from pipeline.schemas import PipelineResult

# Segmentation module (Prince's work)
from pipeline.segmentation.model import load_segmentation_models
from pipeline.segmentation.infer import run_segmentation
from pipeline.segmentation.preprocess import load_image_rgb

# Tissue classification module (Subham's work)
from pipeline.tissue.model import load_tissue_model
from pipeline.tissue.infer import run_tissue_classification

# Healing prediction module (Varsha's work)
from pipeline.healing.model import load_healing_model
from pipeline.healing.infer import run_healing_prediction

logger = logging.getLogger(__name__)

# Configure logging on import so all modules use consistent formatting
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)


class DFUPipeline:
    """
    Main pipeline class. Loads all three models up-front so subsequent
    predictions are fast. Think of it like turning on the machine once
    and then using it for as many images as you want.
    """

    def __init__(self, device=None):
        """
        Load everything: YOLO, MedSAM, ResNet18, XGBoost.
        device=None means "use GPU if available, else CPU".
        Pass device="cpu" to force CPU mode (useful with limited VRAM).
        """
        logger.info("=" * 50)
        logger.info("Loading DFU Pipeline models...")
        logger.info("=" * 50)

        # Segmentation models — YOLO for detection, MedSAM for segmentation
        self.detector, self.sam_model, self.device = load_segmentation_models(device)

        # Tissue classifier — ResNet18 fine-tuned on 3 tissue classes
        self.tissue_model, _ = load_tissue_model(self.device)

        # Healing predictor — XGBoost trained on longitudinal features
        self.healing_model = load_healing_model()

        # Make sure all output folders exist
        ensure_output_dirs()

        logger.info("=" * 50)
        logger.info("Pipeline ready!")
        logger.info("=" * 50)

    def run(self, image_path, case_id="CASE_001", image_id=None,
            simulate_mode="healing", seed=42, save=True) -> PipelineResult:
        """
        Run the full pipeline on a single wound image.

        Args:
            image_path:     path to the wound image (jpg or png)
            case_id:        patient/case identifier (e.g. "CASE_001")
            image_id:       specific image ID — defaults to "<case_id>_DAY0"
            simulate_mode:  "healing" | "non_healing" (for synthetic progression)
            seed:           random seed so results are reproducible
            save:           whether to save all the intermediate files

        Returns:
            PipelineResult containing segmentation, tissue, and healing results.
        """
        if image_id is None:
            image_id = f"{case_id}_DAY0"

        logger.info(f"\n{'='*50}")
        logger.info(f"Running pipeline: {case_id}")
        logger.info(f"Image: {image_path}")
        logger.info(f"{'='*50}")

        # Load image once and pass it through the pipeline in memory.
        # (Reviewer issue 6.2: previously loaded the image twice.)
        img_rgb = load_image_rgb(image_path)

        # ── Step 1: Segmentation ─────────────────────────
        # YOLO finds where the wound is, then MedSAM does the precise outline.
        logger.info("\n[1/3] Segmentation...")
        seg_result = run_segmentation(
            image_path, self.detector, self.sam_model, self.device,
            image_id=image_id, save=save, img_rgb=img_rgb
        )
        logger.info(f"  Area: {seg_result.area_px} px | YOLO conf: {seg_result.yolo_conf:.3f}")

        if seg_result.detection_failed:
            logger.warning("  WARNING: YOLO detection failed — results may be inaccurate")

        # Use the mask directly from memory instead of re-reading from disk
        # (Reviewer issues 1.3, 6.2)
        mask = seg_result.mask

        # ── Step 2: Tissue Classification ────────────────
        # Slide a window over the wound region and classify each patch.
        logger.info("\n[2/3] Tissue Classification...")
        tissue_result = run_tissue_classification(
            img_rgb, mask, self.tissue_model, self.device,
            image_id=image_id, save=save
        )

        if tissue_result.classifier_warning:
            logger.warning(f"  TISSUE WARNING: {tissue_result.classifier_warning}")

        # ── Step 3: Healing Prediction ───────────────────
        # Since we only have one image (Day 0), we generate a synthetic
        # progression forward in time and ask XGBoost to judge it.
        logger.info("\n[3/3] Healing Prediction (simulated progression)...")
        healing_result = run_healing_prediction(
            base_mask=mask,
            healing_model=self.healing_model,
            case_id=case_id,
            tissue_result=tissue_result,
            simulate_mode=simulate_mode,
            seed=seed,
            save=save,
        )

        # ── Pack results into one object ─────────────────
        saved_files = {
            "mask":       seg_result.mask_path,
            "overlay":    seg_result.overlay_path,
            "crop":       seg_result.crop_path,
            "tissue_map": tissue_result.tissue_map_path,
        }

        result = PipelineResult(
            case_id=case_id,
            image_id=image_id,
            segmentation=seg_result,
            tissue=tissue_result,
            healing=healing_result,
            saved_files=saved_files
        )

        # ── Summary ──
        logger.info(f"\n{'='*50}")
        logger.info(f"RESULTS — {case_id}")
        logger.info(f"{'='*50}")
        logger.info(f"  Wound area:      {seg_result.area_px} px")
        logger.info(f"  Tissue:          G={tissue_result.granulation_pct}% "
                     f"S={tissue_result.slough_pct}% N={tissue_result.necrosis_pct}%")
        if tissue_result.classifier_warning:
            logger.info(f"  Tissue note:     {tissue_result.classifier_warning}")
        logger.info(f"  Healing prob:    {healing_result.healing_probability} "
                     f"(simulated {healing_result.simulation_mode})")
        logger.info(f"  Predicted:       {healing_result.predicted_label}")
        logger.info(f"  Rule baseline:   {healing_result.rule_label}")
        logger.info(f"  NOTE: Healing prediction based on simulated progression, "
                     f"not real follow-up data.")
        logger.info(f"{'='*50}\n")

        return result


# ─── Convenience function ────────────────────────────────────────

def run_pipeline(image_path, case_id="CASE_001", simulate_mode="healing",
                 seed=42, device=None) -> PipelineResult:
    """
    One-shot helper: loads models, runs pipeline, returns results.

    WARNING: This reloads all models every call. For repeated use,
    create a DFUPipeline instance once instead:

        pipe = DFUPipeline()
        pipe.run(image1)
        pipe.run(image2)
    """
    warnings.warn(
        "run_pipeline() reloads all models every call. "
        "Create DFUPipeline() once and call .run() instead.",
        DeprecationWarning, stacklevel=2
    )
    pipe = DFUPipeline(device=device)
    return pipe.run(image_path, case_id=case_id,
                    simulate_mode=simulate_mode, seed=seed)
