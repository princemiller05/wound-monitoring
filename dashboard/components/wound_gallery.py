"""
wound_gallery.py
----------------
Shows the patient's actual wound photos pulled back from Blob Storage (via
get_patient_photos, which returns a short-lived image URL per photo) alongside
the analysis for each visit: day, wound area, healing label, tissue mix, and the
patient-reported location / pain / symptoms.

Doctors asked to see the real pictures when they open a patient — this is that.
"""

from datetime import datetime, timezone

import streamlit as st


def _fmt_date(captured_ms) -> str:
    try:
        return datetime.fromtimestamp(int(captured_ms) / 1000,
                                      tz=timezone.utc).strftime("%d %b %Y")
    except Exception:
        return ""


def _label_chip(label: str) -> str:
    label = (label or "pending").lower()
    color = {"healing": "#0E7361", "non_healing": "#C0483F",
             "stable": "#B4830B"}.get(label, "#5F6E69")
    text = {"healing": "Healing", "non_healing": "Non-healing",
            "stable": "Stable"}.get(label, "Pending")
    return (f'<span style="background:{color}1A;color:{color};'
            f'font-size:11px;font-weight:700;padding:3px 9px;border-radius:6px;">'
            f'{text}</span>')


def render_wound_gallery(photos: list) -> None:
    st.markdown('<div class="section-title">🖼️ Wound Photos</div>',
                unsafe_allow_html=True)

    if not photos:
        st.info("No photos uploaded for this patient yet.")
        return

    # Three across; each card = image + its visit analysis.
    cols_per_row = 3
    for start in range(0, len(photos), cols_per_row):
        row = photos[start:start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, ph in zip(cols, row):
            with col:
                url = ph.get("download_url")
                caption = f"Day {ph.get('day_number', 0)} · {_fmt_date(ph.get('captured_ms'))}"
                if url:
                    st.image(url, use_container_width=True, caption=caption)
                else:
                    st.warning("Image unavailable")

                # Analysis line under each photo.
                area_mm2 = ph.get("area_mm2")
                area_px = ph.get("area_px")
                if area_mm2:
                    area_txt = f"{area_mm2:.0f} mm²"
                elif area_px:
                    area_txt = f"{area_px:,} px"
                else:
                    area_txt = "—"

                bits = []
                if ph.get("wound_location"):
                    bits.append(f"📍 {ph['wound_location']}")
                if ph.get("pain_level") is not None:
                    bits.append(f"Pain {ph['pain_level']}/10")
                syms = ph.get("symptoms") or []
                syms = [s for s in syms if s and s.lower() != "none"]
                if syms:
                    bits.append(", ".join(syms))

                st.markdown(
                    f"{_label_chip(ph.get('predicted_label'))} "
                    f"<span style='font-size:12px;color:#5F6E69;'>· {area_txt}</span>",
                    unsafe_allow_html=True,
                )
                if bits:
                    st.markdown(
                        f"<div style='font-size:12px;color:#5F6E69;margin-top:2px;'>"
                        f"{' · '.join(bits)}</div>",
                        unsafe_allow_html=True,
                    )
                if ph.get("notes"):
                    st.markdown(
                        f"<div style='font-size:12px;color:#93A29D;"
                        f"font-style:italic;margin-top:2px;'>“{ph['notes']}”</div>",
                        unsafe_allow_html=True,
                    )
                if ph.get("detection_failed"):
                    st.markdown(
                        "<div style='font-size:11px;color:#C0483F;margin-top:2px;'>"
                        "⚠ Wound not clearly detected in this photo</div>",
                        unsafe_allow_html=True,
                    )
