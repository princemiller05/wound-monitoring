# AI-Assisted Remote Wound Monitoring System for Telehealth Applications

> **Disclaimer:** This is a research prototype developed as a university group project. It is **not** intended for clinical decision-making. The healing prediction is based on simulated wound progression from a single photograph — not real multi-visit patient data. Do not use this system to make medical decisions.

An end-to-end pipeline for analyzing **Diabetic Foot Ulcers (DFUs)** from a single photograph. It segments the wound, classifies the tissue composition, and estimates a healing trajectory.

Built as part of a group project for remote telehealth applications. Three modules — **wound segmentation**, **tissue classification**, and **healing prediction** — chained into one clean pipeline you can run with a single command.

---

## What It Does

Give it a wound photo. Get back:

1. **A segmentation mask** — exactly where the wound is (pixel level)
2. **A tissue breakdown** — how much is granulation (healthy), slough, or necrosis
3. **A healing estimate** — probability score based on simulated 21-day progression

All the intermediate images (masks, overlays, tissue maps, trend plots) get saved to disk so you can see exactly what the pipeline is doing at each step.

---

## Pipeline Overview

```
   Wound Photo
       │
       ▼
┌──────────────────────┐
│  1. Segmentation     │   YOLO finds the wound → MedSAM outlines it precisely
│  (Prince)            │   Outputs: mask, overlay, wound area (px)
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  2. Tissue Classify  │   ResNet18 classifies 64x64 patches (batched)
│  (Subham)            │   as granulation / slough / necrosis
│                      │   Outputs: % of each tissue type, colored heatmap
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  3. Healing Estimate │   Simulates 21-day progression from Day-0 mask,
│  (Varsha)            │   XGBoost predicts healing probability using
│                      │   area + tissue features
│                      │   Outputs: probability, label, area/tissue trend plots
└──────────────────────┘
       │
       ▼
  PipelineResult
```

---

## Repo Structure

```
dfu_pipeline/
├── README.md
├── requirements.txt
├── .gitignore
├── run_demo.py                        # one-command demo
│
├── data/
│   └── sample_inputs/                 # drop wound images here
│
├── models/                            # trained weights go here (not in git)
│   ├── segmentation/
│   │   ├── best.pt                    # YOLO
│   │   └── medsam_vit_b.pth          # MedSAM
│   ├── tissue/
│   │   └── tissue_model.pth          # ResNet18
│   └── healing/
│       └── xgb_healing.json          # XGBoost
│
├── outputs/                           # generated at runtime (gitignored)
│   ├── masks_pred/                    # binary wound masks
│   ├── overlays/                      # contour drawn on original
│   ├── crops/                         # isolated wound, background removed
│   ├── tissue_preds/                  # colored tissue heatmaps
│   └── healing/                       # trend plots + CSVs
│
├── pipeline/
│   ├── __init__.py
│   ├── config.py                      # all paths, thresholds, and settings
│   ├── schemas.py                     # output dataclasses
│   ├── orchestrator.py                # the top-level DFUPipeline class
│   │
│   ├── segmentation/                  # Prince's module
│   │   ├── __init__.py
│   │   ├── model.py                   # loads YOLO + MedSAM
│   │   ├── preprocess.py              # image loading, validation, resizing
│   │   ├── infer.py                   # detection + segmentation
│   │   └── utils.py                   # mask cleanup, overlays, area
│   │
│   ├── tissue/                        # Subham's module
│   │   ├── __init__.py
│   │   ├── model.py                   # loads ResNet18
│   │   ├── preprocess.py              # patch sampling + transforms
│   │   ├── infer.py                   # batched sliding-window classification
│   │   └── utils.py                   # tissue map overlay, percentages
│   │
│   └── healing/                       # Varsha's module
│       ├── __init__.py
│       ├── model.py                   # loads XGBoost
│       ├── synthetic_progression.py   # simulates day 7/14/21 masks
│       ├── features.py                # longitudinal dataset + summary features
│       ├── rule_baseline.py           # 30% area reduction rule
│       ├── infer.py                   # main prediction function
│       └── utils.py                   # trend plots
│
├── notebooks/                         # original notebooks, converted to .py for reference
│   ├── prince_segmentation.py
│   ├── subham_tissue.py
│   └── varsha_healing.py
│
├── scripts/
│   └── train_healing_model.py         # regenerate xgb_healing.json
│
└── tests/
    ├── test_segmentation.py
    ├── test_tissue.py
    └── test_healing.py
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/princemiller05/Wound-Monitoring.git
cd Wound-Monitoring
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Drop in the model weights

The weights aren't committed to the repo (they're too big for git). Place them here:

| File                  | Goes in                     |
|-----------------------|-----------------------------|
| `best.pt`             | `models/segmentation/`      |
| `medsam_vit_b.pth`    | `models/segmentation/`      |
| `tissue_model.pth`    | `models/tissue/`            |
| `xgb_healing.json`    | `models/healing/`           |

If you don't have `xgb_healing.json`, regenerate it:

```bash
python scripts/train_healing_model.py
```

That trains XGBoost on synthetic data with 5-fold cross-validation and saves the model. Takes a few seconds.

---

## Running It

### Quickest way

Put a wound image in `data/sample_inputs/`, then:

```bash
python run_demo.py
```

### On a specific image

```bash
python run_demo.py --image data/sample_inputs/woundtst.jpg --case CASE_001
```

### CPU-only mode

If you don't have a GPU or CUDA is running out of memory:

```bash
python run_demo.py --image data/sample_inputs/woundtst.jpg --device cpu
```

### From Python

```python
from pipeline.orchestrator import DFUPipeline

# Load all models once — this takes a few seconds
pipe = DFUPipeline()

# Then run on as many images as you want — each run is fast
result = pipe.run("data/sample_inputs/woundtst.jpg", case_id="CASE_001")

# Access structured results
print(result.segmentation.area_px)          # e.g. 39246
print(result.tissue.granulation_pct)        # e.g. 85.0
print(result.healing.healing_probability)   # e.g. 0.82
print(result.healing.predicted_label)       # "healing" or "non_healing"
```

### Batch processing many images

```python
from pathlib import Path

pipe = DFUPipeline()

for i, img_path in enumerate(Path("data/sample_inputs").glob("*.jpg")):
    pipe.run(str(img_path), case_id=f"CASE_{i:03d}")
```

---

## Naming Convention

We use a consistent naming scheme across all modules so results can be joined later:

| Field       | Format           | Example          |
|-------------|------------------|------------------|
| `case_id`   | `CASE_NNN`       | `CASE_001`       |
| `image_id`  | `CASE_NNN_DAYN`  | `CASE_001_DAY0`  |
| `wound_id`  | `WN`             | `W1`             |
| `visit_day` | integer          | `0, 7, 14, 21`   |

---

## Output Schemas

Each module returns a typed dataclass (see `pipeline/schemas.py`):

- `SegmentationResult` — `mask_path`, `overlay_path`, `crop_path`, `area_px`, `bbox`, `yolo_conf`, `detection_failed`
- `TissueResult` — `granulation_pct`, `slough_pct`, `necrosis_pct`, `tissue_map_path`, `classifier_warning`
- `HealingResult` — `healing_probability`, `predicted_label`, `rule_label`, `simulation_mode`, `key_factors`
- `PipelineResult` — all three combined

---

## Tests

```bash
cd dfu_pipeline
pytest tests/
```

Tests cover the pure-Python logic (feature extraction, rule baseline, mask postprocessing) plus regression tests that verify the training data has no target leakage. The model-heavy pieces are tested end-to-end by running `run_demo.py` on a sample image.

---

## Healing Model Evaluation

The healing model is evaluated on synthetic simulated trajectories using 5-fold cross-validation. After removing direct target leakage (labels come from a hidden clean trajectory, features from noisy observations), XGBoost achieved approximately 0.92 test accuracy compared with 0.82 for the rule baseline. Tissue features contributed 31% of total feature importance, confirming the model uses tissue composition and not just area change. These results are for research-prototype validation only and should not be interpreted as clinical performance on real patient data.

---

## Known Limitations

This is a research prototype with important constraints that should be understood:

1. **Healing prediction is simulation-based.** The pipeline only takes a single Day-0 image. It generates a synthetic 21-day progression using morphological operations (erosion/dilation) and predicts based on that. This is not a real longitudinal assessment.

2. **Tissue classifier may show bias.** The ResNet18 model was trained on a limited dataset and may over-predict granulation tissue. If the pipeline warns about "classifier collapse," the tissue percentages should not be trusted.

3. **XGBoost is trained on synthetic data.** The healing model learns from artificially generated wound trajectories. While the label assignment uses clinically-grounded thresholds (30% area reduction), the training data does not capture real wound biology.

4. **No calibrated probabilities.** The `healing_probability` score from XGBoost is not calibrated — a score of 0.85 does not mean "85% likely to heal." Platt scaling or isotonic regression would be needed for calibrated outputs.

5. **Single-image limitation.** The pipeline is designed around having one photo per patient. Real clinical assessment requires multiple visits over weeks.

---

## Roadmap

- [x] Unify three notebooks into one pipeline
- [x] End-to-end local inference
- [x] Batched tissue patch classification
- [x] Input validation and format checking
- [x] Python logging (replaces print statements)
- [ ] Real multi-visit longitudinal data support
- [ ] Retrain tissue classifier with balanced dataset
- [ ] Calibrate XGBoost probabilities (Platt scaling)
- [ ] Deploy as a cloud service (REST API with FastAPI)
- [ ] Mobile app for patient-side photo capture

---

## Credits

| Module           | Author   |
|------------------|----------|
| Segmentation     | Prince   |
| Tissue Classify  | Subham   |
| Healing Predict  | Varsha   |
| Pipeline + Infra | Prince   |
