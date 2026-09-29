"""
photo_review.py
---------------
A review-focused photo viewer with simple ◀ / ▶ arrows to step through the
patient's wound photos (oldest → newest), showing the selected image large
alongside that visit's analysis and patient-reported details.
"""

from datetime import datetime, timezone

import streamlit as st


def _fmt_date(captured_ms) -> str:
    try:
        return datetime.fromtimestamp(int(captured_ms) / 1000,
                                      tz=timezone.utc).strftime("%d %b %Y")
    except Exception:
        return ""


def render_photo_review(photos: list, key: str = "") -> None:
    st.markdown('<div class="section-title">Wound photos</div>',
                unsafe_allow_html=True)

    if not photos:
        st.info("No photos uploaded for this patient yet.")
        return

    ordered = sorted(photos, key=lambda p: (p.get("captured_ms", 0),
                                            p.get("day_number", 0)))
    n = len(ordered)

    # Per-patient index; default to the newest photo, reset when patient changes.
    state_key = f"photo_idx_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = n - 1
    idx = max(0, min(st.session_state[state_key], n - 1))

    # ◀  Day X · date (i/n)  ▶
    c_prev, c_mid, c_next = st.columns([1, 3, 1])
    with c_prev:
        if st.button("◀ Prev", use_container_width=True, disabled=idx == 0,
                     key=f"prev_{key}"):
            st.session_state[state_key] = idx - 1
            st.rerun()
    with c_next:
        if st.button("Next ▶", use_container_width=True, disabled=idx == n - 1,
                     key=f"next_{key}"):
            st.session_state[state_key] = idx + 1
            st.rerun()
    ph = ordered[idx]
    with c_mid:
        st.markdown(
            f"<div style='text-align:center;font-weight:600;'>"
            f"Day {ph.get('day_number', 0)} · {_fmt_date(ph.get('captured_ms'))}"
            f"<span style='color:#93A29D;font-weight:400;'> &nbsp;({idx + 1} of "
            f"{n})</span></div>",
            unsafe_allow_html=True)

    img_col, info_col = st.columns([1, 1])
    with img_col:
        url = ph.get("download_url")
        if url:
            st.image(url, use_container_width=True)
        else:
            st.warning("Image unavailable")

    with info_col:
        area_mm2 = ph.get("area_mm2")
        area_px = ph.get("area_px")
        hp = ph.get("healing_probability")
        analyzed = ph.get("analyzed") and (area_px is not None or hp is not None)

        if not analyzed:
            if ph.get("detection_failed"):
                st.warning("⚠ The model couldn't clearly detect a wound in this "
                           "photo, so there are no measurements for it.")
            else:
                st.info("Analysis for this photo isn't available yet — it may "
                        "still be processing, or analysis didn't complete.")

        area_txt = (f"{area_mm2:.0f} mm²" if area_mm2
                    else (f"{area_px:,} px" if area_px else "—"))
        hp_txt = f"{hp * 100:.0f}%" if hp is not None else "—"

        st.markdown(f"**Wound area:** {area_txt}")
        st.markdown(f"**Healing likelihood (this photo):** {hp_txt}")

        tissue_bits = []
        for k2, nm in [("granulation_pct", "Granulation"),
                       ("slough_pct", "Slough"), ("necrosis_pct", "Necrosis")]:
            v = ph.get(k2)
            if v is not None:
                tissue_bits.append(f"{nm} {v:.0f}%")
        if tissue_bits:
            st.markdown("**Tissue:** " + " · ".join(tissue_bits))

        if ph.get("wound_location"):
            st.markdown(f"**Location:** {ph['wound_location']}")
        if ph.get("pain_level") is not None:
            st.markdown(f"**Pain:** {ph['pain_level']}/10")
        syms = [s for s in (ph.get("symptoms") or []) if s and s.lower() != "none"]
        if syms:
            st.markdown("**Symptoms:** " + ", ".join(syms))
        if ph.get("notes"):
            st.markdown(f"**Patient note:** _{ph['notes']}_")
        if ph.get("detection_failed"):
            st.warning("⚠ Wound not clearly detected — measurements may be "
                       "unreliable.")
