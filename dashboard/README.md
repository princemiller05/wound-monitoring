# 🩺 Wound Monitoring – Doctor Dashboard

A premium, production-styled Streamlit dashboard for an AI-powered
Diabetic Foot Ulcer (DFU) monitoring system. Built for clinical
demo / research-prototype use.

> ⚠️ **Research Prototype – Not for Clinical Use.**

## Project Structure

```
wound_dashboard/
├── app.py                     # Main entrypoint — wires pages & components
├── requirements.txt
├── .streamlit/
│   └── config.toml            # Streamlit theme config
├── styles/
│   └── style.css              # Full custom CSS (premium healthcare SaaS look)
├── utils/
│   ├── data_generator.py      # Synthetic patient/clinical data ("backend" layer)
│   └── helpers.py             # Formatting, CSS loading, badge helpers
├── components/
│   ├── sidebar.py              # Left nav: brand + menu
│   ├── kpi_cards.py            # Top KPI summary row
│   ├── patient_search.py       # Search + filters card
│   ├── patient_card.py         # Patient profile card
│   ├── prediction_card.py      # AI healing prediction + gauge
│   ├── ai_insights.py          # Top factors / recommendations / warnings / notes
│   ├── charts.py               # All Plotly chart builders
│   ├── upload_section.py       # Drag-and-drop upload + simulated AI analysis
│   ├── patient_history.py      # Full roster table page
│   ├── reports_section.py      # PDF/CSV export + print
│   └── settings_section.py     # Appearance & localization settings
├── pages/                      # Reserved for future multi-page expansion
├── assets/                     # Logos / static images
└── data/                       # Reserved for cached/exported data
```

## Setup

```bash
cd wound_dashboard
python -m venv venv && source venv/bin/activate   # optional
pip install -r requirements.txt
streamlit run app.py
```

## Design System

- **Palette:** Medical blue (`#1565C0`) on white, with success/warning/danger
  semantic colors for healing status.
- **Cards:** 16–22px rounded corners, soft layered shadows, 1px hairline borders.
- **Typography:** Inter / system sans, bold 700–800 weight headings.
- **Charts:** Plotly, transparent backgrounds, soft gridlines, branded hover tooltips.

## Architecture Notes

- `utils/data_generator.py` is the single point where this prototype's
  synthetic data lives — swap it for real API/database calls without
  touching any UI code.
- All HTML/CSS rendering is isolated inside `components/*.py`, keeping
  `app.py` a thin orchestration layer.
- `st.cache_data` is used for the patient roster to avoid regenerating
  synthetic data on every rerun.
