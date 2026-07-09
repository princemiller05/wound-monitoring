# WoundWatch

A mobile app for people with diabetic foot ulcers (and other slow-healing
wounds) to photograph their wound over time and follow its healing. It's the
patient-facing front end for our Remote Wound Monitoring project — the ML
pipeline (segmentation + tissue + healing prediction) is a separate repo.

> **Heads up — this is Phase 1.** Right now the app runs entirely on *mock*
> data so the whole experience could be built and demoed without waiting on the
> cloud backend. The healing numbers you see are placeholders (they carry a
> "Preview data" badge), and photos are only kept in memory. Real predictions,
> accounts, and cloud storage come in later phases.

## What works today

- Sign up / log in (mock auth — accepts anything for now)
- Patient profile (medical details, clinician info)
- Capture a wound photo with the phone camera
- Tag each photo with a pain level, symptoms, and a note
- Photo history, grouped by week, with pinch-to-zoom
- A progress screen with a wound-area chart, a tissue-composition chart, and a
  healing estimate

## Project layout

Everything lives under `lib/`, split by responsibility so it stays easy to find
things:

```
lib/
├── main.dart              # app entry point + provider/theme wiring
├── models/                # plain data classes (Patient, WoundPhoto, prediction)
├── providers/             # app state (auth + photos) via the `provider` package
├── services/              # data sources — currently just the mock generator
├── screens/               # one file per screen
├── widgets/               # (reserved for shared widgets)
├── theme/                 # colours, text styles, the ThemeData
└── utils/                 # constants (palette, symptom lists, sizes)
```

## State management

I used the `provider` package. Two stores:

- **`AuthProvider`** — who's logged in and their profile.
- **`PhotosProvider`** — the list of wound photos + the latest healing estimate.

Screens `watch` these providers, so when a photo is added from the camera the
home and progress screens rebuild automatically. No manual refreshing.

## Running it

```bash
flutter pub get
flutter run          # with an Android phone plugged in (USB debugging on)
```

Build a shareable APK:

```bash
flutter build apk --release
# -> build/app/outputs/flutter-apk/app-release.apk
```

## What's next (later phases)

- Deploy the ML pipeline as an API and swap the mock prediction for real calls
- Firebase Auth + Firestore so accounts and photos actually persist (per patient)
- Azure Blob storage for the photo files, with secure upload
- Offline photo queue that syncs when back online

## Note

This is a student / research project, not a medical device. It does not diagnose
anything and should not be used for real clinical decisions.
