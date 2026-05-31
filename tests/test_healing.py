"""
Tests for the healing prediction module.

Includes regression tests for target leakage prevention (re-review section 5).
"""

import numpy as np
import pandas as pd
import pytest


def test_healing_sequence_shrinks():
    """Healing sequence masks should progressively shrink."""
    from pipeline.healing.synthetic_progression import generate_healing_sequence

    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 1

    seq = generate_healing_sequence(mask)
    areas = [seq[day].sum() for day in sorted(seq.keys())]

    for i in range(1, len(areas)):
        assert areas[i] <= areas[i - 1], \
            f"Day {sorted(seq.keys())[i]}: area should decrease"


def test_build_features_table():
    """Feature table should produce expected columns."""
    from pipeline.healing.features import build_features_table

    df = pd.DataFrame({
        "wound_id": ["W1"] * 4,
        "day": [0, 7, 14, 21],
        "area_pixels": [1000, 800, 600, 400],
        "granulation_pct": [30, 45, 60, 75],
        "slough_pct": [40, 35, 28, 20],
        "necrosis_pct": [30, 20, 12, 5],
    })

    features = build_features_table(df)

    assert len(features) == 1
    assert "initial_area" in features.columns
    assert "pct_area_change" in features.columns
    assert "area_trend_slope" in features.columns
    assert "mean_granulation" in features.columns
    assert "mean_necrosis" in features.columns
    assert features.iloc[0]["pct_area_change"] == 0.6  # (1000-400)/1000


def test_build_features_table_tissue_features():
    """Tissue features should reflect actual input data."""
    from pipeline.healing.features import build_features_table

    df = pd.DataFrame({
        "wound_id": ["W1"] * 4,
        "day": [0, 7, 14, 21],
        "area_pixels": [1000, 800, 600, 400],
        "granulation_pct": [20, 40, 60, 80],
        "slough_pct": [40, 30, 20, 10],
        "necrosis_pct": [40, 30, 20, 10],
    })

    features = build_features_table(df)
    row = features.iloc[0]

    assert row["mean_granulation"] == 50.0
    assert row["mean_necrosis"] == 25.0
    assert row["granulation_trend"] == 60.0
    assert row["necrosis_trend"] == -30.0


def test_rule_baseline():
    """Rule baseline should classify correctly at threshold."""
    from pipeline.healing.rule_baseline import apply_rule_baseline

    assert apply_rule_baseline(0.35) == "healing"
    assert apply_rule_baseline(0.30) == "healing"
    assert apply_rule_baseline(0.29) == "non_healing"
    assert apply_rule_baseline(0.0) == "non_healing"


def test_longitudinal_dataset():
    """Longitudinal dataset should have correct structure."""
    from pipeline.healing.features import build_longitudinal_dataset

    mask = np.zeros((50, 50), dtype=np.uint8)
    mask[10:40, 10:40] = 1

    masks_dict = {0: mask, 7: mask, 14: mask, 21: mask}
    df = build_longitudinal_dataset("W1", masks_dict)

    assert len(df) == 4
    assert list(df.columns) == [
        "wound_id", "day", "area_pixels",
        "granulation_pct", "slough_pct", "necrosis_pct"
    ]


def test_tissue_progression_uses_real_baseline():
    """Tissue progression should use real Day-0 data when provided."""
    from pipeline.healing.synthetic_progression import generate_tissue_progression

    real_tissue = {"granulation_pct": 85, "slough_pct": 10, "necrosis_pct": 5}
    progression = generate_tissue_progression(
        mode="healing", seed=42, day0_tissue=real_tissue
    )

    day0 = progression[0]
    assert abs(day0["granulation_pct"] - 85) < 10


# ─── Regression tests for target leakage (re-review section 5) ──────────

def test_label_not_identical_to_pct_area_threshold():
    """
    The label must NOT be a deterministic function of pct_area_change.
    If it were, the model could solve the task with one threshold rule
    and accuracy would be perfect (leakage).
    """
    from scripts.train_healing_model import generate_synthetic_training_data
    from pipeline.config import RULE_REDUCTION_THR

    df = generate_synthetic_training_data(n_cases=400, seed=42)
    rule_labels = (df["pct_area_change"] >= RULE_REDUCTION_THR).astype(int)
    assert (df["label"] != rule_labels).sum() > 0, \
        "LEAKAGE: label is identical to the 30% pct_area_change rule"


def test_classes_overlap_near_boundary():
    """
    Both classes should exist near the 30% decision boundary.
    If they don't overlap, the task is trivially separable.
    """
    from scripts.train_healing_model import generate_synthetic_training_data

    df = generate_synthetic_training_data(n_cases=400, seed=42)
    boundary = df[df["pct_area_change"].between(0.15, 0.35)]
    assert boundary["label"].nunique() == 2, \
        "LEAKAGE: only one class exists near the decision boundary"


def test_rule_baseline_not_perfect():
    """
    The simple rule (pct_area_change >= 0.30 → healing) should NOT
    achieve perfect accuracy. If it does, the label is just a copy of
    the rule and XGBoost learns nothing beyond the rule.
    """
    from scripts.train_healing_model import generate_synthetic_training_data
    from pipeline.config import RULE_REDUCTION_THR

    df = generate_synthetic_training_data(n_cases=400, seed=42)
    rule_labels = (df["pct_area_change"] >= RULE_REDUCTION_THR).astype(int)
    rule_accuracy = (rule_labels == df["label"]).mean()
    assert rule_accuracy < 1.0, \
        f"LEAKAGE: rule baseline has perfect accuracy ({rule_accuracy})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
