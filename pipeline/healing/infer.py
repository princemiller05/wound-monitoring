"""
Healing prediction inference.

Takes a Day-0 mask, simulates forward progression, extracts features,
runs XGBoost, and returns the result.

IMPORTANT: Since we typically only have a single Day-0 image, the
"progression" is synthetically generated using mask erosion/dilation.
This means the healing prediction is based on *simulated* data, not
actual follow-up visits. The prediction should be treated as a
demonstration of the pipeline's capability, not a clinical assessment.
"""

import logging
import numpy as np
import pandas as pd

from pipeline.config import FEATURE_COLS, HEALING_THRESHOLD, HEALING_DIR
from pipeline.schemas import HealingResult, TissueResult
from .synthetic_progression import (
    generate_healing_sequence, generate_non_healing_sequence,
    generate_tissue_progression
)
from .features import build_longitudinal_dataset, build_features_table
from .rule_baseline import apply_rule_baseline
from .utils import plot_mask_progression, plot_area_trend, plot_tissue_trend

logger = logging.getLogger(__name__)


def run_healing_prediction(
    base_mask,
    healing_model,
    case_id="CASE_001",
    tissue_result=None,
    simulate_mode="healing",
    seed=42,
    save=True,
) -> HealingResult:
    """
    Predict healing outcome for a single wound.

    Since we usually only have a Day-0 image, we simulate what the wound
    might look like over 21 days and let XGBoost score that trajectory.

    Args:
        base_mask:      Day-0 binary mask from segmentation
        healing_model:  trained XGBoost model
        case_id:        identifier for the patient/case
        tissue_result:  TissueResult from Step 2 — used as Day-0 tissue baseline
        simulate_mode:  "healing" | "non_healing" (no more random "auto")
        seed:           random seed for reproducibility
        save:           save plots + CSVs to outputs/healing/

    Returns:
        HealingResult with probability, predicted label, rule label, key factors.

    NOTE: The prediction is based on simulated progression, not real
    multi-visit data. Do not present this as a clinical prediction.
    """
    rng = np.random.default_rng(seed)

    # ── 1. Generate a synthetic mask sequence across 4 time points ──
    # We always simulate a healing trajectory (erosion) and let the model
    # decide from the features whether it qualifies as "healing" or not.
    # This is more honest than randomly picking a mode.
    if simulate_mode == "healing":
        mask_sequence = generate_healing_sequence(base_mask, seed=seed)
    else:
        mask_sequence = generate_non_healing_sequence(base_mask, seed=seed)

    # ── 2. Generate tissue composition trajectory ──
    # If we have real tissue classification from Step 2, use it as the
    # Day-0 baseline and simulate progression from there.
    # Otherwise fall back to fully synthetic tissue data.
    if tissue_result is not None:
        tissue_progression = generate_tissue_progression(
            mode=simulate_mode,
            seed=seed,
            day0_tissue={
                "granulation_pct": tissue_result.granulation_pct,
                "slough_pct": tissue_result.slough_pct,
                "necrosis_pct": tissue_result.necrosis_pct,
            }
        )
        logger.info("  [healing] Using real Day-0 tissue from classifier as baseline")
    else:
        tissue_progression = generate_tissue_progression(
            mode=simulate_mode, seed=seed
        )
        logger.info("  [healing] No tissue result provided — using fully synthetic tissue")

    # ── 3. Build the longitudinal dataset (row per day) ──
    longitudinal_df = build_longitudinal_dataset(
        wound_id=case_id,
        masks_dict=mask_sequence,
        tissue_dict=tissue_progression
    )

    # ── 4. Build the feature row (one per wound) ──
    features_df = build_features_table(longitudinal_df)
    if len(features_df) == 0:
        raise ValueError("Feature table is empty — check mask quality")

    # ── 5. Run XGBoost ──
    X = features_df[FEATURE_COLS]
    healing_prob = float(healing_model.predict_proba(X)[0][1])   # P(healing)
    predicted_label = "healing" if healing_prob >= HEALING_THRESHOLD else "non_healing"

    # ── 6. Rule-based baseline for comparison ──
    pct_change = float(features_df.iloc[0]["pct_area_change"])
    rule_label = apply_rule_baseline(pct_change)

    # ── 7. Pull the top features from XGBoost importances ──
    try:
        importances = healing_model.feature_importances_
        importance_pairs = sorted(
            zip(FEATURE_COLS, importances),
            key=lambda x: x[1], reverse=True
        )
        key_factors = [name for name, _ in importance_pairs[:3]]
    except Exception:
        key_factors = []

    # ── 8. Save plots + CSVs ──
    saved_files = {}
    if save:
        HEALING_DIR.mkdir(parents=True, exist_ok=True)

        try:
            mask_plot = str(HEALING_DIR / f"{case_id}_mask_progression.png")
            plot_mask_progression(mask_sequence, mask_plot, case_id)
            saved_files["mask_progression"] = mask_plot

            area_plot = str(HEALING_DIR / f"{case_id}_area_trend.png")
            plot_area_trend(longitudinal_df, area_plot, case_id)
            saved_files["area_trend"] = area_plot

            tissue_plot = str(HEALING_DIR / f"{case_id}_tissue_trend.png")
            plot_tissue_trend(longitudinal_df, tissue_plot, case_id)
            saved_files["tissue_trend"] = tissue_plot

            long_csv = str(HEALING_DIR / f"{case_id}_longitudinal.csv")
            longitudinal_df.to_csv(long_csv, index=False)
            saved_files["longitudinal_csv"] = long_csv

            feat_csv = str(HEALING_DIR / f"{case_id}_features.csv")
            features_df.to_csv(feat_csv, index=False)
            saved_files["features_csv"] = feat_csv
        except PermissionError:
            logger.warning("  [healing] Could not save some files (disk write blocked)")
            logger.warning("  [healing] Results are still computed, just not saved to disk.")

    logger.info(f"  [healing] prob={healing_prob:.3f} label={predicted_label} "
                f"rule={rule_label} mode={simulate_mode}")
    logger.info("  [healing] NOTE: prediction based on simulated progression, "
                "not real multi-visit data")

    return HealingResult(
        case_id=case_id,
        healing_probability=round(healing_prob, 4),
        predicted_label=predicted_label,
        rule_label=rule_label,
        simulation_mode=simulate_mode,
        key_factors=key_factors,
        features=features_df.iloc[0].to_dict() if len(features_df) > 0 else None
    )
