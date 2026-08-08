# WoundWatch Azure Functions (Prince)

The serverless backend that connects the app to the model and the database.

## The flow

```
App                Blob Storage           Function                 Firestore
 │  get upload URL   │                       │                        │
 ├──────────────────────────────────────────► get_upload_url         │
 │  ◄── SAS URL ─────┤                       │                        │
 │  PUT photo ──────►│ (wound-photos/…)      │                        │
 │                   │  blob created ───────►│ on_image_uploaded      │
 │                   │                       │  → calls ML endpoint    │
 │                   │                       │  → writes result ──────►│
 │  get history ─────────────────────────────► get_patient_history ──►│ (reads)
 │  ◄── latest_prediction ───────────────────┤                        │
```

## The three functions

| Function | Trigger | What it does |
|----------|---------|--------------|
| `get_upload_url` | HTTP GET | Returns a short-lived SAS URL so the app can upload one photo to Blob without ever holding the storage key. |
| `on_image_uploaded` | Blob trigger (`wound-photos/{name}`) | On every upload: base64s the photo, calls the ML endpoint, writes the per-photo result to `wound_photos/{image_id}`, then rebuilds `patients/{id}.latest_prediction` (the longitudinal trend). |
| `get_patient_history` | HTTP GET | Returns a patient's `latest_prediction` for the app and the doctor dashboard. |

## Filename rule (important)

Everything keys off the blob name. The app uploads each photo as:

```
{patient_id}/{patient_id}_DAY{n}_{timestamp_ms}.jpg
e.g.  CASE_001/CASE_001_DAY7_1723100000000.jpg
```

`on_image_uploaded` reads the patient id and day number straight from that path.
The trailing millisecond timestamp makes every photo a **unique** record, so
nothing overwrites and multiple photos on the same day coexist honestly (with
their true capture times). The healing trend keeps **one point per day** — if
there are several photos on a day, the most recent one is used.

## Endpoint contract (as deployed)

The live ML endpoint takes a **base64 image** (not a path) and returns
segmentation + tissue + healing for that one photo. There is no "aggregate"
mode, so the day-by-day trend is built here from the stored per-photo results.

```jsonc
// request
{ "image_base64": "...", "case_id": "CASE_001", "image_id": "CASE_001_DAY7",
  "simulate_mode": "healing", "seed": 42, "save": false }
```

## App settings (Function App → Configuration)

Set these on the Function App. **Never commit them.**

| Setting | Used by | Where it comes from |
|---------|---------|---------------------|
| `AZURE_STORAGE_CONNECTION_STRING` | blob trigger | Storage account → Access keys |
| `AZURE_STORAGE_ACCOUNT_NAME` | get_upload_url | Storage account name |
| `AZURE_STORAGE_ACCOUNT_KEY` | get_upload_url | Storage account → Access keys |
| `ML_ENDPOINT_URI` | on_image_uploaded | Shubam's scoring URL |
| `ML_ENDPOINT_KEY` | on_image_uploaded | Shubam's endpoint primary key |
| `FIREBASE_CREDENTIALS` | inference + history | Firebase → Project settings → Service accounts → the JSON, pasted as one string |

## Deploy

```bash
# from azure/functions/
func azure functionapp publish <your-function-app-name>
```

Then in the app, set `functionBaseUrl` in `lib/services/api_config.dart` to
`https://<your-function-app-name>.azurewebsites.net/api` and rebuild.

> Local logic was validated end-to-end with `azure/local_test_pipeline.py`
> (endpoint call + Firestore writes + trend aggregation) before deployment.
