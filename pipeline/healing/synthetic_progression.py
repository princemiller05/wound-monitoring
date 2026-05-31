"""
Synthetic longitudinal wound progression.

Since we usually only have ONE image per patient (day 0), we simulate
what the wound might look like on days 7, 14, and 21 so XGBoost has
enough time points to work with.

CAVEAT: This uses simple morphological operations (erosion/dilation)
which don't capture real wound healing biology (irregular granulation,
depth changes, edge effects). This is acceptable for a demo pipeline
but should not be presented as biologically accurate simulation.
In a real deployment, actual follow-up images would replace this.
"""

import cv2
import numpy as np

from pipeline.config import HEALING_DAYS


def generate_healing_sequence(base_mask: np.ndarray, seed=42) -> dict:
    """
    Simulate a wound that IS healing.
    We shrink the mask a little more every week by eroding it.

    Returns:
        {day: mask} — e.g. {0: ..., 7: ..., 14: ..., 21: ...}
    """
    kernel = np.ones((7, 7), np.uint8)
    sequence = {HEALING_DAYS[0]: base_mask.copy()}

    current = base_mask.copy()
    for i, day in enumerate(HEALING_DAYS[1:], 1):
        current = cv2.erode(current, kernel, iterations=2 * i)
        # Ensure mask stays valid (at least some pixels)
        if current.sum() < 50:
            current = sequence[HEALING_DAYS[i - 1]].copy()
        sequence[day] = current.copy()

    return sequence


def generate_non_healing_sequence(base_mask: np.ndarray, seed=42) -> dict:
    """
    Simulate a wound that is NOT healing.
    Area bounces around a bit but never really shrinks — stagnant wound.
    """
    kernel = np.ones((5, 5), np.uint8)
    sequence = {
        HEALING_DAYS[0]: base_mask.copy(),
        HEALING_DAYS[1]: cv2.erode(base_mask, kernel, iterations=1),
        HEALING_DAYS[2]: cv2.dilate(base_mask, kernel, iterations=1),
        HEALING_DAYS[3]: base_mask.copy(),   # back to original size
    }
    return sequence


def generate_tissue_progression(mode="healing", seed=42,
                                 day0_tissue=None) -> dict:
    """
    Simulate how tissue composition changes over time.

    If day0_tissue is provided (from the real ResNet18 classifier output),
    we use it as the starting point and simulate realistic changes from there.
    Otherwise we fall back to fully synthetic values.

    Args:
        mode:         "healing" or "non_healing"
        seed:         random seed for noise
        day0_tissue:  optional dict with granulation_pct, slough_pct, necrosis_pct
                      from the actual tissue classifier (Step 2)

    Returns:
        {day: {"granulation_pct": ..., "slough_pct": ..., "necrosis_pct": ...}}
    """
    rng = np.random.default_rng(seed)

    if day0_tissue is not None:
        # Use real classifier output as Day-0 baseline
        g0 = day0_tissue.get("granulation_pct", 30)
        s0 = day0_tissue.get("slough_pct", 40)
        n0 = day0_tissue.get("necrosis_pct", 30)

        if mode == "healing":
            # Healing: granulation increases toward 100, necrosis/slough decrease toward 0.
            # Use headroom-based increments so values never saturate at exactly 100
            # (re-review section 8.1)
            g_headroom = 100 - g0
            s_floor = s0  # slough can drop toward 0
            n_floor = n0  # necrosis can drop toward 0
            progression = {
                0:  {"granulation_pct": g0, "slough_pct": s0, "necrosis_pct": n0},
                7:  {"granulation_pct": g0 + 0.25 * g_headroom, "slough_pct": s0 - 0.25 * s_floor, "necrosis_pct": n0 - 0.30 * n_floor},
                14: {"granulation_pct": g0 + 0.50 * g_headroom, "slough_pct": s0 - 0.45 * s_floor, "necrosis_pct": n0 - 0.55 * n_floor},
                21: {"granulation_pct": g0 + 0.75 * g_headroom, "slough_pct": s0 - 0.65 * s_floor, "necrosis_pct": n0 - 0.75 * n_floor},
            }
        else:
            # Non-healing: tissue composition stagnates
            progression = {
                0:  {"granulation_pct": g0, "slough_pct": s0, "necrosis_pct": n0},
                7:  {"granulation_pct": g0 + 2, "slough_pct": s0 + 3, "necrosis_pct": n0 - 5},
                14: {"granulation_pct": g0 - 2, "slough_pct": s0 + 2, "necrosis_pct": n0},
                21: {"granulation_pct": g0, "slough_pct": s0, "necrosis_pct": n0},
            }
    else:
        # Fully synthetic — no real tissue data available
        if mode == "healing":
            progression = {
                0:  {"granulation_pct": 30, "slough_pct": 40, "necrosis_pct": 30},
                7:  {"granulation_pct": 45, "slough_pct": 35, "necrosis_pct": 20},
                14: {"granulation_pct": 60, "slough_pct": 28, "necrosis_pct": 12},
                21: {"granulation_pct": 75, "slough_pct": 20, "necrosis_pct":  5},
            }
        else:
            progression = {
                0:  {"granulation_pct": 20, "slough_pct": 35, "necrosis_pct": 45},
                7:  {"granulation_pct": 22, "slough_pct": 38, "necrosis_pct": 40},
                14: {"granulation_pct": 18, "slough_pct": 37, "necrosis_pct": 45},
                21: {"granulation_pct": 20, "slough_pct": 35, "necrosis_pct": 45},
            }

    # Add noise and clamp to valid range [0, 100]
    for day in progression:
        for key in progression[day]:
            noise = rng.normal(0, 2)
            progression[day][key] = max(0, min(100, progression[day][key] + noise))

    return progression
