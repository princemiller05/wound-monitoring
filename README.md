# Wound Monitoring

**AI-Assisted Remote Wound Monitoring System for Telehealth Applications**

> **Disclaimer — research prototype, not for clinical use.** This is a university group project. It is **not** intended for clinical decision-making. The healing prediction comes from a small model trained on synthetic wound progression and is **not calibrated**. Do not use this system to make medical decisions.

Wound Monitoring is an end-to-end system for tracking **Diabetic Foot Ulcers (DFUs)** from photographs over time. It segments the wound, classifies the tissue, and estimates whether the wound is **healing or worsening** across visits. Patients capture photos in the **WoundWatch** mobile app; a cloud pipeline analyses each upload automatically; and a doctor reviews each patient's progress on a web dashboard.

> **Project vs app name:** the **project** is *Wound Monitoring*; the patient **mobile app** is *WoundWatch*. "WoundWatch" only ever refers to the app.

---

## Two parts of this project

| Part | What it is | Where it lives |
|------|------------|----------------|
| **The ML pipeline** | The original local pipeline: segmentation → tissue → healing. Runs with one command. | `pipeline/` |
| **The cloud system** | The pipeline deployed on Azure ML as an event-driven, multi-patient service, plus the app wiring and a doctor dashboard. | `azure/`, `dashboard/` |

The pipeline code is unchanged by the cloud move — everything new is additive.

---

## What it does

Give it a series of wound photos taken on different days. Get back:

1. **A segmentation mask** — exactly where the wound is (pixel level)
2. **A tissue breakdown** — granulation (healthy) / slough / necrosis percentages
3. **A healing estimate** — a probability and a plain `improving / worsening / stable` trend across the visits

All intermediate images (masks, overlays, tissue maps, trend plots) are saved so you can see what each step is doing.

---

## How the cloud system works

The system is **event-driven** and handles **many patients at once**. An upload triggers analysis; analysis writes to the database; the app and dashboard simply read what is stored.

```
WRITE PATH  (runs automatically on every single upload)

  Patient takes a photo in the WoundWatch app
        |  upload -> wound-photos/CASE_001/CASE_001_DAY7.jpg
        v
  [Azure Blob Storage] --- new blob event ---> [on-image-uploaded Function]
        |                                          (Prince)
        |  1. analyse THIS photo (segmentation + tissue)
        v
  [Azure ML endpoint -> score.py]  --> area_px + tissue %  (stored on the photo doc)
        |
        |  2. aggregate all of the patient's stored numbers (XGBoost only)
        v
  [Azure ML endpoint -> score.py]  --> healing probability + label + trend
        |
        v
  [Firestore]  patients/CASE_001.latest_prediction  (the longitudinal summary)


READ PATH  (instant; nothing is recomputed)

  [WoundWatch app]  Progress screen  ─┐
                                       ├─> get-patient-history?patient_id=CASE_001
  [Doctor dashboard] pick a patient  ─┘            (Prince)
                                                       |
                                                       v
                              charts + improving/worsening badge
```

**Ad-hoc uploads:** the doctor dashboard can also upload photos directly through a `predict-direct` Function (Shubam), which runs the full pipeline on the spot without touching the database.

**Many patients at once:** each patient has their own Blob folder and Firestore documents, so data never mixes. The Azure ML endpoint **autoscales** (min 2 / max 6 instances) and uploads are independent events, so ~10 apps uploading together queue and drain rather than fail.

---

## Architecture at a glance

| Layer | Component | Owner |
|-------|-----------|-------|
| Clients | WoundWatch app (patients) + desktop doctor dashboard (view + ad-hoc upload) | Prince + Varsha |
| Image storage | Azure Blob Storage container `wound-photos` (private, one folder per patient) | Prince |
| Database | Firestore — per-photo results + per-patient longitudinal summary | Prince |
| Event trigger | `on-image-uploaded` Function — runs the model on every upload, writes results | Prince |
| Read / ad-hoc APIs | `get-patient-history` (stored results) + `predict-direct` (ad-hoc) | Prince + Shubam |
| Brain | Azure ML managed online endpoint running `score.py`, autoscaled | Shubam |
| Models | 4 registered models: YOLO, MedSAM, ResNet18, XGBoost | Prince + Shubam + Varsha |

> **Azure resource names** keep the `woundwatch-*` prefix from the original app guide (resource group `woundwatch-rg`, storage `woundwatchstorage`, function app `woundwatch-api`, ML workspace `woundwatch-ml`) so the already-built app keeps working. The project name is *Wound Monitoring*; the resource prefix is just a legacy identifier.

---

## Repo structure

```
Wound-Monitoring/
├── README.md
├── requirements.txt
├── run_demo.py                         # one-command local demo
│
├── pipeline/                           # the ML pipeline (unchanged by the cloud move)
│   ├── config.py                       # paths, thresholds, FEATURE_COLS
│   ├── schemas.py                      # output dataclasses
│   ├── orchestrator.py                 # DFUPipeline class
│   ├── segmentation/                   # YOLO + MedSAM        (Prince)
│   ├── tissue/                         # ResNet18             (Shubam)
│   └── healing/                        # XGBoost + features   (Varsha)
│
├── models/                             # weights — NOT in git (see Setup)
│   ├── segmentation/{best.pt, medsam_vit_b.pth}
│   ├── tissue/tissue_model.pth
│   └── healing/xgb_healing.json
│
├── scripts/train_healing_model.py      # regenerate xgb_healing.json
├── tests/                              # pytest suite
│
├── azure/                              # NEW — cloud deployment (additive)
│   ├── score.py                        # scoring script: single / longitudinal / aggregate   (Shubam)
│   ├── environment.yml                 # conda env (torch + MedSAM + opencv-headless)         (Shubam)
│   ├── endpoint.yml, deployment.yml    # managed online endpoint definitions                  (Shubam)
│   └── functions/
│       ├── host.json
│       ├── requirements.txt            # azure-functions, requests, firebase-admin, azure-storage-blob
│       ├── on_image_uploaded/          # Blob-trigger inference + DB writes                   (Prince)
│       ├── get_patient_history/        # read stored results for app + dashboard              (Prince)
│       └── predict_direct/             # ad-hoc dashboard uploads                             (Shubam)
│
└── dashboard/                          # NEW — Streamlit doctor dashboard                     (Varsha)
    ├── app.py
    └── requirements.txt
```

---

## The team & branch workflow

One shared repo, one branch per person, Shubam reviews and merges.

| Branch | Owner | Responsibility |
|--------|-------|----------------|
| `shubam-integration` | **Shubam** | Tissue model, `score.py`, the Azure ML endpoint + scaling, `predict-direct`, end-to-end & load testing. Reviews and merges PRs. |
| `prince-segmentation` | **Prince** | Segmentation models, the app, Blob Storage, the Firestore database, the `on-image-uploaded` trigger, and `get-patient-history`. |
| `varsha-healing` | **Varsha** | The healing model and the doctor dashboard. |

```bash
git checkout -b your-branch        # work on your own branch
git add . && git commit -m "..."   # commit your work
git push -u origin your-branch     # push, then open a PR for Shubam to merge
```

Detailed step-by-step deployment guides (one per person) live alongside this repo:

- `01_Shubam_Integration_Lead_Azure_ML.docx`
- `02_Prince_Segmentation_and_App_Azure_ML.docx`
- `03_Varsha_Healing_Prediction_Azure_ML.docx`

---

## Local setup

### 1. Clone

```bash
git clone https://github.com/NaskenAI/Wound-Monitoring.git
cd Wound-Monitoring
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add the model weights

Weights are too big for git, so they are **not** committed. Place them here:

| File | Goes in |
|------|---------|
| `best.pt` | `models/segmentation/` |
| `medsam_vit_b.pth` | `models/segmentation/` |
| `tissue_model.pth` | `models/tissue/` |
| `xgb_healing.json` | `models/healing/` |

If you don't have `xgb_healing.json`, regenerate it (takes a few seconds):

```bash
python scripts/train_healing_model.py
```

---

## Running it locally

```bash
# quickest: drop an image in data/sample_inputs/ then
python run_demo.py

# on a specific image
python run_demo.py --image data/sample_inputs/woundtst.jpg --case CASE_001

# CPU-only (no GPU / CUDA OOM)
python run_demo.py --image data/sample_inputs/woundtst.jpg --device cpu
```

From Python:

```python
from pipeline.orchestrator import DFUPipeline

pipe = DFUPipeline()                                   # loads all models once
result = pipe.run("data/sample_inputs/woundtst.jpg", case_id="CASE_001")

print(result.segmentation.area_px)          # e.g. 39246
print(result.tissue.granulation_pct)        # e.g. 85.0
print(result.healing.healing_probability)   # e.g. 0.82
print(result.healing.predicted_label)       # "healing" or "non_healing"
```

---

## Deploying to Azure (overview)

The full instructions are in the three deployment guides above. In short:

1. **Register four models** in Azure ML (`dfu-yolo`, `dfu-medsam`, `dfu-tissue`, `dfu-healing`).
2. **Build the environment** (`dfu-inference`) and deploy `score.py` to a **managed online endpoint** with autoscaling — Shubam.
3. **Set up the database fields** in Firestore and deploy the **`on-image-uploaded`** Blob trigger so the model runs on every upload — Prince.
4. **Deploy `get-patient-history`** and point the app's Progress screen at it; deploy **`predict-direct`** for the dashboard — Prince + Shubam.
5. **Build the doctor dashboard** and connect it to `get-patient-history` and `predict-direct` — Varsha.
6. **Test** the write path, the read path, and the **10-patient load test**.

---

## Naming convention

| Field | Format | Example |
|-------|--------|---------|
| `case_id` (patient) | `CASE_NNN` | `CASE_001` |
| `image_id` | `CASE_NNN_DAYN` | `CASE_001_DAY7` |
| Blob path | `{patient_id}/{patient_id}_DAY{n}.jpg` | `CASE_001/CASE_001_DAY7.jpg` |
| `visit_day` | integer | `0, 7, 14, 21` |

> The whole pipeline keys off the **filename** to know which photo is which day, so the app's upload path must follow the Blob path format exactly.

---

## Output schema

Each module returns a typed dataclass (`pipeline/schemas.py`). The stored cloud result the app and dashboard read looks like:

```json
{
  "healing_probability": 0.82,
  "predicted_label": "healing",
  "trend": "improving",
  "top_factors": ["Wound area reducing across visits", "..."],
  "day_series": [0, 7, 14],
  "area_series": [39246, 35110, 31044],
  "tissue_series": { "granulation": [...], "slough": [...], "necrosis": [...] },
  "is_mock": false
}
```

---

## Tests

```bash
pytest tests/
```

Tests cover the pure-Python logic (feature extraction, rule baseline, mask postprocessing) plus regression tests guarding against target leakage in the training data. Model-heavy pieces are tested end-to-end via `run_demo.py`.

---

## Known limitations

1. **Healing model trained on synthetic data.** Labels use clinically-grounded thresholds (30% area reduction), but the training data does not capture real wound biology.
2. **Probabilities are not calibrated.** A score of 0.85 does **not** mean "85% likely to heal." Platt scaling / isotonic regression would be needed.
3. **Tissue classifier may be biased** toward granulation on limited data. If the pipeline warns about "classifier collapse," do not trust the tissue percentages.
4. **Longitudinal accuracy depends on real visits.** The cloud system uses real multi-visit photos (an improvement over the original single-image simulation), but a meaningful trend still needs several photos over time.
5. **Not a medical device.** Research prototype only.

---

## Credits

| Module | Author |
|--------|--------|
| Segmentation, app, database & backend | Prince |
| Tissue classification & integration | Shubam |
| Healing prediction & doctor dashboard | Varsha |

Final-year ECE group project · VTU.
