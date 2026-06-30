"""
Azure ML Managed Online Endpoint scoring script.

Expected request JSON:
{
    "image_path": "path/to/local/image.jpg",
    "case_id": "CASE_001",
    "image_id": "CASE_001_DAY0",
    "simulate_mode": "healing",
    "seed": 42,
    "save": false
}
"""

import json
import os
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.orchestrator import DFUPipeline


pipeline = None


class ValidationError(ValueError):
    """Raised when the request payload is missing or invalid."""


def init():
    """Load the DFU pipeline once when the Azure ML worker starts."""
    global pipeline

    device = os.getenv("DFU_DEVICE") or None
    pipeline = DFUPipeline(device=device)


def run(raw_data):
    """Parse request JSON, run inference, and return JSON-serializable output."""
    try:
        if pipeline is None:
            raise RuntimeError("DFUPipeline is not initialized. Azure ML should call init() before run().")

        payload = _parse_payload(raw_data)
        image_path = _resolve_image_input(payload)

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
        return _error_response("InternalError", str(exc))


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

    Currently supports only local image paths. Future source types such as
    Blob Storage URLs or uploaded bytes can be added here without changing run().
    """
    image_path = payload.get("image_path")
    if image_path:
        return image_path

    if payload.get("blob_url"):
        raise ValidationError("blob_url input is not implemented yet. Provide image_path for now.")

    if payload.get("image_bytes") or payload.get("image_base64"):
        raise ValidationError("uploaded image bytes are not implemented yet. Provide image_path for now.")

    raise ValidationError("Missing required image input. Provide image_path.")


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
    if isinstance(value, np.ndarray):
        return None

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    return value
