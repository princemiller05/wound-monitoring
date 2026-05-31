"""
Build the feature tables that XGBoost needs.

Two levels:
  1. Longitudinal dataset — one row per (wound, day) — all the raw measurements
  2. Feature table — one row per wound — summary stats used for prediction

The feature table includes both area-based features (how wound size changes)
and tissue-based features (how tissue composition changes). This ensures
the tissue classifier's output actually influences the healing prediction.
"""

import logging
import numpy as np
import pandas as pd

from pipeline.config import FEATURE_COLS

logger = logging.getLogger(__name__)


def build_longitudinal_dataset(wound_id: str, masks_dict: dict,
                                tissue_dict: dict = None) -> pd.DataFrame:
    """
    Build a row-per-day dataframe for a single wound.

    Args:
        wound_id:    identifier string (e.g. "W1" or "CASE_001")
        masks_dict:  {day: mask} from either real visits or synthetic progression
        tissue_dict: optional {day: {"granulation_pct", ...}}

    Returns:
        DataFrame with columns:
        wound_id, day, area_pixels, granulation_pct, slough_pct, necrosis_pct
    """
    rows = []
    for day in sorted(masks_dict.keys()):
        mask = masks_dict[day]
        area = int(np.sum(mask > 0))   # count wound pixels

        row = {
            "wound_id": wound_id,
            "day": day,
            "area_pixels": area,
        }

        # Pull in tissue data if available, otherwise default to zeros.
        if tissue_dict and day in tissue_dict:
            row["granulation_pct"] = tissue_dict[day].get("granulation_pct", 0)
            row["slough_pct"]      = tissue_dict[day].get("slough_pct", 0)
            row["necrosis_pct"]    = tissue_dict[day].get("necrosis_pct", 0)
        else:
            row["granulation_pct"] = 0.0
            row["slough_pct"]      = 0.0
            row["necrosis_pct"]    = 0.0

        rows.append(row)

    return pd.DataFrame(rows)


def build_features_table(longitudinal_df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse the per-day data into one row per wound with summary features.

    Features (must match FEATURE_COLS in config.py and training script):
        Area-based:
        - initial_area        — area on day 0
        - final_area          — area on last day
        - pct_area_change     — fraction change (positive = shrinking = good)
        - mean_area           — average across all days
        - area_trend_slope    — linear regression slope (more stable than std)

        Tissue-based (from the actual ResNet18 classifier output):
        - mean_granulation    — average granulation % across time points
        - mean_necrosis       — average necrosis % across time points
        - granulation_trend   — change in granulation from first to last day
        - necrosis_trend      — change in necrosis from first to last day
    """
    features = []

    for wound_id, group in longitudinal_df.groupby("wound_id"):
        group = group.sort_values("day")
        areas = group["area_pixels"].values

        initial = areas[0]
        final = areas[-1]
        # pct_area_change: positive means wound shrank, negative means it grew
        change = (initial - final) / initial if initial > 0 else 0.0

        # Linear regression slope, normalized by initial area so it's
        # comparable across wound sizes (re-review section 8.2).
        # A slope of -0.05 means the wound shrinks by 5% of initial area per step.
        if len(areas) >= 2:
            raw_slope = float(np.polyfit(range(len(areas)), areas, 1)[0])
            slope = raw_slope / initial if initial > 0 else 0.0
        else:
            slope = 0.0

        # Tissue composition features
        gran_vals = group["granulation_pct"].values
        necro_vals = group["necrosis_pct"].values

        feat = {
            "wound_id": wound_id,
            "initial_area": initial,
            "final_area": final,
            "pct_area_change": round(change, 6),
            "mean_area": round(float(np.mean(areas)), 2),
            "area_trend_slope": round(slope, 6),
            "mean_granulation": round(float(np.mean(gran_vals)), 2),
            "mean_necrosis": round(float(np.mean(necro_vals)), 2),
            "granulation_trend": round(float(gran_vals[-1] - gran_vals[0]), 2),
            "necrosis_trend": round(float(necro_vals[-1] - necro_vals[0]), 2),
        }
        features.append(feat)

    return pd.DataFrame(features)
