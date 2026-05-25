"""
Load Varsha's XGBoost healing model.

This was trained on longitudinal features (how wound area and tissue
composition change over time) and outputs a probability between
0 (non-healing) and 1 (healing).

NOTE: Trained on synthetic data. See README for limitations.
"""

import logging
import xgboost as xgb

from pipeline.config import HEALING_MODEL_PATH

logger = logging.getLogger(__name__)


def load_healing_model():
    """
    Load XGBoost from JSON. We use save_model/load_model (not pickle)
    because it's the portable XGBoost way — works across versions.
    """
    model = xgb.XGBClassifier()
    model.load_model(str(HEALING_MODEL_PATH))

    logger.info("[healing] XGBoost model loaded")
    return model
