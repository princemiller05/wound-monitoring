"""
Azure ML Managed Online Endpoint scoring script.

Expected request JSON (supply exactly one image source):
{
    "image_base64": "<base64-encoded JPEG / PNG / BMP / TIFF>",
    "image_path": "path/to/local/image.jpg",
    "case_id": "CASE_001",
    "image_id": "CASE_001_DAY0",
    "simulate_mode": "healing",
    "seed": 42,
    "save": false
}
"""

import base64
import json
import logging
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.orchestrator import DFUPipeline


logger = logging.getLogger(__name__)

pipeline = None

# Magic-number prefixes for the formats pipeline.config.SUPPORTED_FORMATS allows.
# An uploaded payload has to be written to a file whose suffix is one of these,
# because pipeline.segmentation.preprocess.validate_image_path() rejects any
# other extension before the image is ever decoded.
_IMAGE_MAGIC = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"BM", ".bmp"),
    (b"II*\x00", ".tiff"),
    (b"MM\x00*", ".tiff"),
)


class ValidationError(ValueError):
    """Raised when the request payload is missing or invalid."""


def init():
    """Load the DFU pipeline once when the Azure ML worker starts."""
    global pipeline

    device = os.getenv("DFU_DEVICE") or None
    pipeline = DFUPipeline(device=device)


def run(raw_data):
    """Parse request JSON, run inference, and return JSON-serializable output."""
    temp_path = None
    try:
        if pipeline is None:
            raise RuntimeError("DFUPipeline is not initialized. Azure ML should call init() before run().")

        payload = _parse_payload(raw_data)
        image_path, temp_path = _resolve_image_input(payload)

        result = pipeline.run(
            image_path=image_path,
            case_id=payload.get("case_id", "CASE_001"),
            image_id=payload.get("image_id"),
            simulate_mode=payload.get("simulate_mode", "healing"),
            seed=_parse_seed(payload.get("seed", 42)),
            save=_parse_bool(payload.get("save", False)),
        )

        return {
            "status": "success",
            "result": _pipeline_result_to_json(result),
        }
    except ValidationError as exc:
        return _error_response("ValidationError", str(exc))
    except Exception as exc:
        logger.exception("pipeline.run failed")
        return _error_response("InternalError", str(exc))
    finally:
        # Uploaded payloads are materialised on disk for the pipeline to read.
        # Drop them once the request is done, or a long-lived replica slowly
        # fills its disk with decoded images.
        if temp_path:
            _safe_unlink(temp_path)


def _parse_payload(raw_data):
    if isinstance(raw_data, dict):
        return raw_data

    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode("utf-8")

    if isinstance(raw_data, str):
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSON request body: {exc.msg}") from exc

        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object.")

        return payload

    raise ValidationError("Request body must be a JSON object, JSON string, or UTF-8 encoded JSON bytes.")


def _resolve_image_input(payload):
    """
    Resolve the image source for DFUPipeline.run().

    Returns (image_path, temp_path). temp_path is None for inputs the caller
    already had on disk, and is the path we created for uploaded payloads so
    run() can delete it afterwards.
    """
    image_path = payload.get("image_path")
    if image_path:
        return image_path, None

    if payload.get("image_base64"):
        temp_path = _decode_base64_image(payload["image_base64"])
        return temp_path, temp_path

    if payload.get("blob_url"):
        raise ValidationError("blob_url input is not implemented yet. Provide image_base64 or image_path.")

    if payload.get("image_bytes"):
        raise ValidationError("image_bytes input is not implemented yet. Provide image_base64 or image_path.")

    raise ValidationError("Missing required image input. Provide image_base64 or image_path.")


def _decode_base64_image(value):
    """
    Decode a base64 image payload onto disk and return its path.

    Everything the pipeline could not recover from is surfaced as a
    ValidationError so the caller gets a 200 with a useful message rather than
    an opaque InternalError: malformed base64, an empty payload, or bytes that
    are not an image in a supported format.
    """
    if isinstance(value, bytes):
        try:
            value = value.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValidationError("image_base64 must be an ASCII base64 string.") from exc

    if not isinstance(value, str):
        raise ValidationError("image_base64 must be a base64-encoded string.")

    encoded = value.strip()
    if not encoded:
        raise ValidationError("image_base64 is empty.")

    # Browser clients routinely send a data URI rather than a bare payload.
    if encoded.startswith("data:"):
        _, _, encoded = encoded.partition(",")
        encoded = encoded.strip()
        if not encoded:
            raise ValidationError("image_base64 data URI contains no payload.")

    # Drop MIME line wrapping first, so validate=True rejects only genuinely
    # invalid base64 instead of legal line breaks.
    compact = "".join(encoded.split())

    try:
        data = base64.b64decode(compact, validate=True)
    except (ValueError, TypeError) as exc:
        # binascii.Error (bad padding, characters outside the alphabet)
        # subclasses ValueError.
        raise ValidationError(f"image_base64 is not valid base64: {exc}") from exc

    if not data:
        raise ValidationError("image_base64 decoded to zero bytes.")

    suffix = _sniff_image_suffix(data)
    if suffix is None:
        raise ValidationError(
            "image_base64 did not decode to a recognised image. "
            "Supported formats: JPEG, PNG, BMP, TIFF."
        )

    upload_dir = Path(os.getenv("DFU_OUTPUT_DIR", "/tmp/outputs")) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix="upload_", suffix=suffix, dir=str(upload_dir))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    except Exception:
        _safe_unlink(temp_path)
        raise

    logger.info("decoded image_base64 to %s (%d bytes)", temp_path, len(data))
    return temp_path


def _sniff_image_suffix(data):
    """Return a SUPPORTED_FORMATS suffix for these bytes, or None if unknown."""
    for magic, suffix in _IMAGE_MAGIC:
        if data.startswith(magic):
            return suffix

    return None


def _safe_unlink(path):
    """Best-effort cleanup — never let a failed delete mask the real result."""
    try:
        os.unlink(path)
    except OSError:
        logger.warning("could not remove temporary upload %s", path, exc_info=True)


def _parse_seed(value):
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("seed must be an integer.") from exc


def _parse_bool(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False

    if isinstance(value, int) and value in {0, 1}:
        return bool(value)

    raise ValidationError("save must be a boolean.")


def _error_response(error_type, message):
    return {
        "status": "error",
        "error_type": error_type,
        "message": message,
    }


def _pipeline_result_to_json(result):
    return {
        "case_id": result.case_id,
        "image_id": result.image_id,
        "segmentation": {
            "image_id": result.segmentation.image_id,
            "mask_path": result.segmentation.mask_path,
            "overlay_path": result.segmentation.overlay_path,
            "crop_path": result.segmentation.crop_path,
            "area_px": _json_safe(result.segmentation.area_px),
            "bbox": _json_safe(result.segmentation.bbox),
            "yolo_conf": _json_safe(result.segmentation.yolo_conf),
            "detection_failed": _json_safe(result.segmentation.detection_failed),
        },
        "tissue": {
            "image_id": result.tissue.image_id,
            "granulation_pct": _json_safe(result.tissue.granulation_pct),
            "slough_pct": _json_safe(result.tissue.slough_pct),
            "necrosis_pct": _json_safe(result.tissue.necrosis_pct),
            "tissue_map_path": result.tissue.tissue_map_path,
            "total_patches": _json_safe(result.tissue.total_patches),
            "classifier_warning": result.tissue.classifier_warning,
        },
        "healing": {
            "case_id": result.healing.case_id,
            "healing_probability": _json_safe(result.healing.healing_probability),
            "predicted_label": result.healing.predicted_label,
            "rule_label": result.healing.rule_label,
            "simulation_mode": result.healing.simulation_mode,
            "key_factors": _json_safe(result.healing.key_factors),
            "features": _json_safe(result.healing.features),
        },
        "saved_files": _json_safe(result.saved_files),
    }


def _json_safe(value):
    """
    Convert pipeline output into something json.dumps() can always encode.

    Arrays are walked element by element instead of being handed to .tolist().
    On an object-dtype array .tolist() returns the Python objects it holds
    as-is, so nested ndarrays and NumPy scalars survive unconverted; recursing
    guarantees every leaf passes through the np.generic and float branches.
    """
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _json_safe(value.item())

        return [_json_safe(item) for item in value]

    if isinstance(value, np.generic):
        # .item() yields a plain Python scalar. Recurse so that a non-finite
        # np.float* is still caught by the float branch below.
        return _json_safe(value.item())

    if isinstance(value, float):
        # NaN and +/-inf are not valid JSON: json.dumps() emits bare NaN and
        # Infinity tokens, which strict client parsers reject.
        return value if math.isfinite(value) else None

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    return value
