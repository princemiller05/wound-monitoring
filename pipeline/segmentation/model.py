"""
Load the segmentation models: YOLO + MedSAM.

YOLO finds the wound (gives us a bounding box), then MedSAM takes that
box as a prompt and produces a pixel-precise mask. Works way better than
either model alone.
"""

import logging
import torch
from ultralytics import YOLO
from segment_anything import sam_model_registry

from pipeline.config import YOLO_WEIGHTS, MEDSAM_CHECKPOINT

logger = logging.getLogger(__name__)


def load_segmentation_models(device=None):
    """
    Load both models and put them on the right device.

    Args:
        device: torch device, or None to auto-pick (cuda if available)

    Returns:
        detector:  YOLO model (stays in eval mode by default)
        sam_model: MedSAM model in eval mode
        device:    whichever device we ended up using
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        device = torch.device(device)

    # Load YOLO — this one figures out its own device internally
    detector = YOLO(str(YOLO_WEIGHTS))

    # Load MedSAM — using the vit_b (base) variant which is the smallest
    sam_model = sam_model_registry["vit_b"](checkpoint=str(MEDSAM_CHECKPOINT))
    sam_model.to(device)
    sam_model.eval()

    logger.info(f"[segmentation] Models loaded on {device}")
    return detector, sam_model, device
