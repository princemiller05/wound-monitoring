"""
Small helpers for loading and prepping images before segmentation.
Kept separate from infer.py so they're easy to reuse elsewhere.
"""

import logging
from pathlib import Path

import cv2
import numpy as np

from pipeline.config import SUPPORTED_FORMATS, MAX_IMAGE_PIXELS

logger = logging.getLogger(__name__)


def validate_image_path(path: str) -> Path:
    """
    Check that the image path is valid, the file exists,
    and it's a supported format. Raises clear errors if not.
    """
    p = Path(path).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    if p.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format '{p.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    return p


def load_image_rgb(path: str) -> np.ndarray:
    """
    Load an image from disk in RGB order with input validation.
    OpenCV reads in BGR by default (legacy reasons), which is annoying,
    so we convert it here to keep everything downstream in RGB.
    """
    validated_path = validate_image_path(path)

    img = cv2.imread(str(validated_path))
    if img is None:
        raise FileNotFoundError(f"Could not decode image: {path}")

    # Check image isn't absurdly large (e.g. 50MP medical camera raw)
    h, w = img.shape[:2]
    if h * w > MAX_IMAGE_PIXELS:
        logger.warning(
            f"  [preprocess] Image is {w}x{h} ({w*h/1e6:.1f}MP) — "
            f"downscaling to cap memory usage"
        )
        scale = (MAX_IMAGE_PIXELS / (h * w)) ** 0.5
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h))

    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def resize_to_1024(img_rgb: np.ndarray) -> np.ndarray:
    """MedSAM was trained on 1024x1024 images — everything has to fit that."""
    return cv2.resize(img_rgb, (1024, 1024))
