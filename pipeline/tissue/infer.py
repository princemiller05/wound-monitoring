"""
Tissue classification inference.
Slides patches across the wound region and classifies each one.

Uses batched inference for performance: all patches are collected,
stacked into a single tensor, and run through ResNet18 in one forward
pass. This is 10-50x faster than classifying patches one at a time.
"""

import logging
import cv2
import torch
import numpy as np

from pipeline.config import (
    TISSUE_CLASSES, TISSUE_PATCH_SIZE, TISSUE_STEP,
    TISSUE_PRED_DIR
)
from pipeline.schemas import TissueResult
from .preprocess import sample_patches, prepare_patch_tensor
from .utils import compute_tissue_percentages, create_tissue_overlay

logger = logging.getLogger(__name__)


@torch.no_grad()   # inference only
def classify_patches(image_rgb, mask, model, device,
                     patch_size=TISSUE_PATCH_SIZE, step=TISSUE_STEP):
    """
    Walk across the wound, collect all patches, classify them in one
    batched forward pass for efficiency.

    Returns:
        class_counts: how many patches were classified as each class
        predictions:  list of (y, x, class_name) for drawing the overlay later
    """
    class_counts = {cls: 0 for cls in TISSUE_CLASSES}
    predictions = []

    # Collect all patches and their positions first
    all_patches = []
    all_positions = []
    for patch, y, x in sample_patches(image_rgb, mask, patch_size, step):
        all_patches.append((patch, y, x))
        all_positions.append((y, x))

    if not all_patches:
        return class_counts, predictions

    # Stack all patches into a single batch tensor for one forward pass
    # This is 10-50x faster than running the model patch-by-patch
    batch = torch.stack([
        prepare_patch_tensor(p, device).squeeze(0)
        for p, _, _ in all_patches
    ])

    # Single batched forward pass through ResNet18
    outputs = model(batch)
    preds = outputs.argmax(dim=1).cpu().numpy()

    # Map predictions back to positions
    for idx, (y, x) in enumerate(all_positions):
        class_name = TISSUE_CLASSES[preds[idx]]
        class_counts[class_name] += 1
        predictions.append((y, x, class_name))

    return class_counts, predictions


def _check_classifier_collapse(class_counts: dict) -> str:
    """
    Check if the classifier is only predicting one class (collapsed model).
    Returns a warning string if collapse detected, empty string otherwise.
    """
    total = sum(class_counts.values())
    if total == 0:
        return "No patches classified — wound region may be too small"

    for cls, count in class_counts.items():
        if count == total:
            return (f"Classifier predicted '{cls}' for all {total} patches. "
                    f"This indicates the model may not be properly trained "
                    f"to distinguish all 3 tissue types. Tissue percentages "
                    f"should be interpreted with caution.")

    # Also warn if one class dominates >95% of predictions
    for cls, count in class_counts.items():
        if count / total > 0.95:
            return (f"Classifier predicted '{cls}' for {count}/{total} patches "
                    f"({count/total*100:.0f}%). Results may not be reliable.")

    return ""


def run_tissue_classification(image_rgb, mask, model, device,
                              image_id="image", save=True) -> TissueResult:
    """
    Top-level tissue classification function.
    Classifies all patches in a single batched forward pass,
    computes percentages, checks for classifier collapse,
    optionally saves a visualization, and returns a TissueResult.
    """
    class_counts, predictions = classify_patches(
        image_rgb, mask, model, device
    )

    pct = compute_tissue_percentages(class_counts)
    total_patches = sum(class_counts.values())
    tissue_map_path = ""

    # Check for classifier collapse (reviewer issue C2)
    classifier_warning = _check_classifier_collapse(class_counts)
    if classifier_warning:
        logger.warning(f"  [tissue] WARNING: {classifier_warning}")

    # Save the visual overlay if requested
    if save and total_patches > 0:
        try:
            overlay = create_tissue_overlay(image_rgb, mask, predictions)
            tissue_map_path = str(TISSUE_PRED_DIR / f"{image_id}_tissue_map.png")
            cv2.imwrite(tissue_map_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
        except PermissionError:
            logger.warning("  [tissue] Could not save overlay (disk write blocked)")

    logger.info(f"  [tissue] G={pct['granulation_pct']:.1f}% "
                f"S={pct['slough_pct']:.1f}% N={pct['necrosis_pct']:.1f}% "
                f"({total_patches} patches)")

    return TissueResult(
        image_id=image_id,
        granulation_pct=pct["granulation_pct"],
        slough_pct=pct["slough_pct"],
        necrosis_pct=pct["necrosis_pct"],
        tissue_map_path=tissue_map_path,
        total_patches=total_patches,
        classifier_warning=classifier_warning,
    )
