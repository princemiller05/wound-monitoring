"""
The actual segmentation inference: YOLO detection -> MedSAM segmentation.

YOLO gives us a rough bounding box around the wound. MedSAM then uses
that box as a prompt to produce a precise pixel-level mask.
"""

import logging
import cv2
import numpy as np
import torch

from pipeline.config import (
    SEG_INPUT_SIZE, SEG_THRESHOLD, YOLO_CONF, BBOX_PAD,
    MASKS_DIR, OVERLAYS_DIR, CROPS_DIR
)
from pipeline.schemas import SegmentationResult
from .preprocess import load_image_rgb, resize_to_1024
from .utils import postprocess_mask, extract_wound_crop, create_overlay, compute_area
from .calibration import pixels_per_mm, area_mm2

logger = logging.getLogger(__name__)


@torch.no_grad()   # inference only — no need to track gradients
def segment_wound(img_rgb, yolo_model, sam_model, device,
                  threshold=SEG_THRESHOLD, pad=BBOX_PAD):
    """
    Run the full detection -> segmentation pipeline on one image.

    Args:
        img_rgb:    H x W x 3 numpy array in RGB
        yolo_model: loaded YOLO detector
        sam_model:  loaded MedSAM model
        device:     torch device
        threshold:  probability cutoff to binarize the mask
        pad:        pixels of padding to add around the YOLO bbox

    Returns:
        mask:             1024x1024 binary mask (uint8)
        yolo_conf:        YOLO confidence (0.0 if YOLO missed)
        bbox:             [x1, y1, x2, y2] the bbox we used (in 1024 space)
        detection_failed: True if YOLO found nothing and we used a fallback
    """
    H, W = img_rgb.shape[:2]
    yolo_conf = 0.0
    detection_failed = False

    # ── Step 1: YOLO finds the wound bbox ────────────────
    results = yolo_model(img_rgb, conf=YOLO_CONF, verbose=False)
    boxes = results[0].boxes

    if len(boxes) == 0:
        # YOLO didn't find anything — fall back to the centre of the frame.
        # Flag this clearly so downstream callers know the result is unreliable.
        detection_failed = True
        logger.warning("  [seg] YOLO found no wound — falling back to centre crop. "
                       "Detection confidence set to 0.0.")
        # BUGFIX (#35): the prompt box must be in MedSAM's 1024x1024 space, NOT
        # the original image size. Building it from W/H left the box far outside
        # the 1024 frame on large photos, so MedSAM segmented almost everything
        # (one case produced a mask over 90% of the image). Use the middle half
        # of the 1024 frame directly — the same 25% region, correctly scaled.
        q = SEG_INPUT_SIZE // 4
        bbox = np.array([q, q, 3 * q, 3 * q], dtype=np.float32)
    else:
        # Pick the highest-confidence detection
        best = boxes[boxes.conf.argmax()]
        x1, y1, x2, y2 = best.xyxy[0].cpu().numpy()
        yolo_conf = float(best.conf.item())

        # Scale the bbox from the original image size to 1024 (MedSAM's input size)
        scale_x = SEG_INPUT_SIZE / W
        scale_y = SEG_INPUT_SIZE / H
        # Expand the bbox a bit with padding so MedSAM has some context
        bbox = np.array([
            max(0, x1 * scale_x - pad),
            max(0, y1 * scale_y - pad),
            min(SEG_INPUT_SIZE, x2 * scale_x + pad),
            min(SEG_INPUT_SIZE, y2 * scale_y + pad)
        ])
        logger.info(f"  [seg] YOLO conf={yolo_conf:.3f} bbox={bbox.astype(int)}")

    # ── Step 2: MedSAM segments the wound using the bbox as prompt ──
    img_1024 = resize_to_1024(img_rgb)
    # Convert to tensor: HWC uint8 -> 1CHW float in [0, 1]
    img_t = (torch.from_numpy(img_1024)
             .permute(2, 0, 1).unsqueeze(0).float().to(device) / 255.0)
    bbox_t = torch.as_tensor(bbox, dtype=torch.float32).unsqueeze(0).to(device)

    # MedSAM is made of three parts: image encoder, prompt encoder, mask decoder
    emb = sam_model.image_encoder(img_t)
    sparse, dense = sam_model.prompt_encoder(
        points=None, boxes=bbox_t, masks=None
    )
    logits, _ = sam_model.mask_decoder(
        image_embeddings=emb,
        image_pe=sam_model.prompt_encoder.get_dense_pe(),
        sparse_prompt_embeddings=sparse,
        dense_prompt_embeddings=dense,
        multimask_output=False   # only want one mask
    )

    # Sigmoid -> probability map -> resize -> threshold
    prob = cv2.resize(
        torch.sigmoid(logits).squeeze().cpu().numpy(),
        (SEG_INPUT_SIZE, SEG_INPUT_SIZE)
    )
    mask = (prob > threshold).astype(np.uint8)

    # Clean up stray pixels and smooth edges
    mask = postprocess_mask(mask)

    return mask, yolo_conf, bbox.astype(int).tolist(), detection_failed


def run_segmentation(image_path, yolo_model, sam_model, device,
                     image_id="image", save=True,
                     img_rgb=None) -> SegmentationResult:
    """
    High-level entry point. Loads the image, runs segmentation,
    optionally saves all the outputs to disk, and returns a structured result.

    Args:
        image_path:  path to the wound image
        img_rgb:     optional pre-loaded image array (avoids double-loading)
    """
    # Use pre-loaded image if provided, otherwise load from disk
    if img_rgb is None:
        img_rgb = load_image_rgb(image_path)

    mask, yolo_conf, bbox, detection_failed = segment_wound(
        img_rgb, yolo_model, sam_model, device
    )

    area_px = compute_area(mask)

    # #30 — detect the ArUco marker on the SAME 1024 image the mask uses, so the
    # scale matches, and convert the pixel area into real mm² (None if no marker).
    img_1024 = resize_to_1024(img_rgb)
    ppm = pixels_per_mm(img_1024)
    area_real_mm2 = area_mm2(area_px, ppm)

    mask_path = ""
    overlay_path = ""
    crop_path = ""

    if save:
        try:
            # 1. Binary mask as PNG (multiplied by 255 so it's visible)
            mask_path = str(MASKS_DIR / f"{image_id}_mask.png")
            cv2.imwrite(mask_path, mask * 255)

            # 2. Green contour drawn on the original image
            overlay = create_overlay(img_rgb, mask)
            overlay_path = str(OVERLAYS_DIR / f"{image_id}_overlay.png")
            cv2.imwrite(overlay_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

            # 3. Just the wound, cropped and background-zeroed
            crop = extract_wound_crop(img_rgb, mask)
            crop_path = str(CROPS_DIR / f"{image_id}_crop.png")
            cv2.imwrite(crop_path, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
        except PermissionError:
            logger.warning("  [seg] Could not save some files (disk write blocked)")

    return SegmentationResult(
        image_id=image_id,
        mask_path=mask_path,
        overlay_path=overlay_path,
        crop_path=crop_path,
        area_px=area_px,
        bbox=bbox,
        yolo_conf=yolo_conf,
        detection_failed=detection_failed,
        pixels_per_mm=ppm,
        area_mm2=area_real_mm2,
        mask=mask,
    )
