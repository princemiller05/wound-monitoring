"""
Item #30 — Turn a pixel count into a real measurement (mm²).

A wound's area in pixels changes every time the phone is held closer or farther,
so the same wound gives different numbers on different days — useless for
tracking healing. The fix: place a printed ArUco marker of KNOWN size (e.g. a
20 mm square) next to the wound. Detect it, work out how many pixels equal one
millimetre, and convert the mask's pixel area into real mm².

All measurements are done on the SAME 1024x1024 image the mask is computed on,
so the scale matches the mask exactly.

Usage:
    ppm = pixels_per_mm(img_1024)          # None if no marker found
    area = area_mm2(area_px, ppm)          # None if uncalibrated
"""

import logging

import cv2
import numpy as np

from pipeline.config import ARUCO_DICT_NAME, ARUCO_MARKER_MM

logger = logging.getLogger(__name__)


def _get_detector():
    """
    Build an ArUco detector that works across OpenCV versions.
    OpenCV >= 4.7 uses the ArucoDetector class; older versions use the
    functional detectMarkers(). Returns (mode, obj) where mode says which API.
    """
    dict_id = getattr(cv2.aruco, ARUCO_DICT_NAME, cv2.aruco.DICT_4X4_50)
    if hasattr(cv2.aruco, "ArucoDetector"):
        aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
        params = cv2.aruco.DetectorParameters()
        return "new", cv2.aruco.ArucoDetector(aruco_dict, params)
    # Older API
    aruco_dict = cv2.aruco.Dictionary_get(dict_id)
    params = cv2.aruco.DetectorParameters_create()
    return "old", (aruco_dict, params)


def _detect_corners(img_rgb):
    """Return the 4 corner points (Nx2) of the first ArUco marker, or None."""
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    try:
        mode, obj = _get_detector()
        if mode == "new":
            corners, ids, _ = obj.detectMarkers(gray)
        else:
            aruco_dict, params = obj
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray, aruco_dict, parameters=params)
    except Exception as exc:  # aruco module missing, etc.
        logger.warning(f"  [calib] ArUco detection unavailable: {exc}")
        return None

    if ids is None or len(corners) == 0:
        return None
    return corners[0].reshape(4, 2)


def pixels_per_mm(img_rgb):
    """
    How many pixels equal one millimetre, from the marker's known size.
    Returns None if no marker is visible (result is then reported in px only).
    """
    corners = _detect_corners(img_rgb)
    if corners is None:
        return None
    # Average the four side lengths (robust to slight perspective).
    sides = [float(np.linalg.norm(corners[i] - corners[(i + 1) % 4]))
             for i in range(4)]
    px_side = sum(sides) / 4.0
    if px_side <= 0 or ARUCO_MARKER_MM <= 0:
        return None
    ppm = px_side / ARUCO_MARKER_MM
    logger.info(f"  [calib] marker found: {ppm:.2f} px/mm")
    return ppm


def area_mm2(area_px, ppm):
    """Convert a pixel area to mm² using pixels-per-mm. None if uncalibrated."""
    if not ppm or ppm <= 0:
        return None
    return round(area_px / (ppm * ppm), 1)
