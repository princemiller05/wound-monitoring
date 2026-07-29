"""
config.py
=========
All the paths, thresholds, and settings for the DFU pipeline live here.
Keeping them in one file means we don't have to dig through the code
every time we want to change a path or tune a threshold.
"""

import logging
import os
from pathlib import Path

# ─── Logging Setup ─────────────────────────────────────────────
# Use Python logging instead of print() so callers can control verbosity.
# Set to logging.DEBUG for development, logging.WARNING for production.
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_LEVEL = logging.INFO

# ─── Project Root ───────────────────────────────────────────────
# This resolves to the dfu_pipeline/ folder no matter where you run from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ─── Model Paths ────────────────────────────────────────────────
# Where the trained model weights live. Drop the files here.
MODELS_DIR = Path(os.getenv("AZUREML_MODEL_DIR")) / "models" if os.getenv("AZUREML_MODEL_DIR") else PROJECT_ROOT / "models"

YOLO_WEIGHTS       = MODELS_DIR / "segmentation" / "best.pt"              # YOLO wound detector
MEDSAM_CHECKPOINT  = MODELS_DIR / "segmentation" / "medsam_vit_b.pth"     # MedSAM segmenter
TISSUE_MODEL_PATH  = MODELS_DIR / "tissue" / "tissue_model.pth"           # ResNet18 tissue classifier
HEALING_MODEL_PATH = MODELS_DIR / "healing" / "xgb_healing.json"          # XGBoost healing predictor

# ─── Data Paths ─────────────────────────────────────────────────
DATA_DIR    = PROJECT_ROOT / "data"
SAMPLE_DIR  = DATA_DIR / "sample_inputs"   # put test images here

# ─── Output Paths ───────────────────────────────────────────────
# Everything the pipeline generates goes under OUTPUT_DIR.
# Default to /tmp/outputs: on Azure ML Managed Online Endpoints the
# application directory (/var/azureml-app) is mounted read-only, so writing
# there makes init() fail. Set DFU_OUTPUT_DIR to write somewhere else.
OUTPUT_DIR       = Path(os.getenv("DFU_OUTPUT_DIR", "/tmp/outputs"))
MASKS_DIR        = OUTPUT_DIR / "masks_pred"      # binary wound masks
OVERLAYS_DIR     = OUTPUT_DIR / "overlays"        # contour-on-image visualizations
CROPS_DIR        = OUTPUT_DIR / "crops"           # isolated wound crops
TISSUE_PRED_DIR  = OUTPUT_DIR / "tissue_preds"    # tissue classification maps
HEALING_DIR      = OUTPUT_DIR / "healing"         # healing plots + CSVs
METRICS_DIR      = OUTPUT_DIR / "metrics"         # reserved for eval metrics

# ─── Input Validation ──────────────────────────────────────────
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
MAX_IMAGE_PIXELS  = 50_000_000  # reject images larger than ~50MP to cap memory

# ─── Segmentation Settings ──────────────────────────────────────
SEG_INPUT_SIZE    = 1024   # MedSAM was trained on 1024x1024 inputs, don't change
SEG_THRESHOLD     = 0.5    # probability cutoff to binarize the mask
YOLO_CONF         = 0.25   # YOLO confidence threshold (lower = more detections)
BBOX_PAD          = 30     # extra padding around YOLO bbox before passing to MedSAM

# ─── Tissue Classification Settings ─────────────────────────────
TISSUE_PATCH_SIZE = 64     # size of each patch we classify
TISSUE_STEP       = 32     # stride of the sliding window (smaller = slower but denser)
TISSUE_CLASSES    = ["granulation", "necrosis", "slough"]
TISSUE_INPUT_SIZE = 224    # what ResNet18 expects after resizing
TISSUE_MEAN       = [0.485, 0.456, 0.406]   # ImageNet normalization
TISSUE_STD        = [0.229, 0.224, 0.225]

# Color map used when drawing the tissue classification overlay.
# Yellow for slough matches Subham's training labels (gran_mask=[255,0,0],
# slough_mask=[255,255,0], necro_mask=[0,0,0]).
TISSUE_COLORS = {
    "granulation": (255, 0, 0),     # red    — healthy healing tissue
    "necrosis":    (0, 0, 0),       # black  — dead tissue (bad sign)
    "slough":      (255, 255, 0),   # yellow — dead skin / wound fluid
}

# ─── Healing Prediction Settings ────────────────────────────────
HEALING_DAYS       = [0, 7, 14, 21]   # the days in each longitudinal sequence
HEALING_THRESHOLD  = 0.5              # XGBoost prob cutoff: >= this → "healing"
RULE_REDUCTION_THR = 0.30             # clinical rule: 30% area reduction = healing

# Columns that go into the XGBoost model (must match training!)
# Includes both area-based and tissue-based features so the tissue
# classifier's output actually influences the healing prediction.
FEATURE_COLS = [
    "initial_area",
    "final_area",
    "pct_area_change",        # renamed from pct_area_reduction (can be negative)
    "mean_area",
    "area_trend_slope",       # linear regression slope (replaces noisy std_area)
    "mean_granulation",       # avg granulation % across time points
    "mean_necrosis",          # avg necrosis % across time points
    "granulation_trend",      # change in granulation from first to last day
    "necrosis_trend",         # change in necrosis from first to last day
]

# ─── Naming Convention ──────────────────────────────────────────
# Keep IDs consistent across all three modules so data can be joined later:
#     case_id   = "CASE_001"         (one patient case)
#     image_id  = "CASE_001_DAY0"    (a specific visit / photo)
#     wound_id  = "W1"               (internal wound identifier)
#     visit_day = 0                  (day number, integer)


def ensure_output_dirs():
    """Create every output directory on startup so we don't crash later."""
    for d in [MASKS_DIR, OVERLAYS_DIR, CROPS_DIR,
              TISSUE_PRED_DIR, HEALING_DIR, METRICS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
