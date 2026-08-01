# Wound Monitoring – Doctor Dashboard

A production-quality Streamlit dashboard for an AI-powered Diabetic Foot
Ulcer (DFU) monitoring system, styled to feel like a premium healthcare
SaaS product (Apollo / Microsoft Healthcare / Philips / Epic-grade UI).

> ⚠️ **Research Prototype — Not for Clinical Use.**

## Project Structure

```
wound_dashboard/
├── app.py                     # Entry point: page config, routing, layout
├── requirements.txt
├── styles/
│   └── custom.css             # Full custom theme (cards, KPIs, badges, nav)
├── utils/
│   ├── data_generator.py      # Synthetic patient + visit data (replace with EMR/API)
│   └── helpers.py             # CSS loader, badge/trend formatting helpers
├── components/
│   ├── sidebar_nav.py         # Branded sidebar navigation
│   ├── kpi_cards.py           # Top KPI summary cards
│   ├── patient_card.py        # Patient profile card
│   ├── prediction_card.py     # AI healing-prediction gauge card
│   ├── insight_cards.py       # Top factors / recommendations / warnings / notes
│   ├── charts.py              # All Plotly chart builders
│   ├── upload_section.py      # Drag-and-drop image upload + analyse flow
│   └── footer.py              # Global footer bar
├── pages_logic/
│   ├── dashboard.py           # Main dashboard page
│   ├── patient_history.py     # Searchable patient roster + distributions
│   ├── upload_images.py       # Image upload & analysis results page
│   ├── ai_analysis.py         # Deep-dive AI explainability page
│   ├── reports.py             # PDF / CSV export & print
│   └── settings.py            # Appearance, notifications, account settings
└── assets/                    # Place logo/images here if needed
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- All patient data is **synthetically generated** (`utils/data_generator.py`)
  for demonstration purposes. Swap this module for real EMR / Azure ML /
  database calls in production.
- The UI is fully restyled via `styles/custom.css` — no default Streamlit
  appearance is used anywhere (sidebar, buttons, inputs, tabs, uploader,
  cards are all custom-themed with a medical-blue palette).
- PDF generation uses `reportlab` if installed; otherwise falls back to a
  plain-text byte stream so the app never breaks.
- Architecture cleanly separates **UI (components/pages_logic)** from
  **business/data logic (utils)** for maintainability and testability.
