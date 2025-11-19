# app.py
# Water Intake Tracker — pandas-free, matplotlib-free, pure-SVG chart
# - Persists to local CSV (date,ml)
# - Daily goal 3000 ml
# - Quick-add buttons + manual add
# - Weekly SVG bar chart (no pandas, no numpy)
# Run: streamlit run app.py

from __future__ import annotations
import streamlit as st
from datetime import date, timedelta, datetime
from pathlib import Path
import csv
import io
import html

DATA_FILE = Path("water_data.csv")
DAILY_GOAL_ML = 3000

st.set_page_config(page_title="Water Intake Tracker", page_icon="💧", layout="wide")

# ----------------- Persistence helpers (CSV, no pandas) -----------------
def read_data_rows():
    """Return list of rows as tuples (date_obj, ml_int)."""
    if not DATA_FILE.exists():
        return []
    rows = []
    try:
        with DATA_FILE.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    d = datetime.strptime(r["date"], "%Y-%m-%d").date()
                    m = int(r["ml"])
                    rows.append((d, m))
                except Exception:
                    # skip malformed rows
                    continue
    except Exception:
        return []
    return rows

def save_data_rows(rows: list[tuple[date, int]]):
    """Write rows (date_obj, ml_int) to CSV sorted by date ascending."""
    rows_sorted = sorted(rows, key=lambda x: (x[0], x[1]))
    with DATA_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "ml"])
        for d, m in rows_sorted:
            writer.writerow([d.isoformat(), str(int(m))])

def append_entry(entry_date: date, ml: int):
    rows = read_data_rows()
    rows.append((entry_date, int(ml)))
    save_data_rows(rows)

def clear_today_entries():
    rows = read_data_rows()
    today = date.today()
    rows = [r for r in rows if r[0] != today]
    save_data_rows(rows)

def clear_all_history():
    if DATA_FILE.exists():
        try:
            DATA_FILE.unlink()
        except Exception:
            save_data_rows([])

# ----------------- Business helpers -----------------
def get_today_total(rows=None):
    if rows is None:
        rows = read_data_rows()
    today = date.today()
    return sum(m for d, m in rows if d == today)

def get_week_totals(reference=None, rows=None):
    """Return list of (date_obj, total_ml_for_date) for 7-day window ending at reference (inclusive)."""
    if reference is None:
        reference = date.today()
    if rows is None:
        rows = read_data_rows()
    totals = {}
    for d, m in rows:
        totals.setdefault(d, 0)
        totals[d] += int(m)
    days = [reference - timedelta(days=i) for i in range(6, -1, -1)]
    out = [(d, totals.get(d, 0)) for d in days]
    return out

def format_ml(x: int) -> str:
    if x >= 1000:
        return f"{x/1000:.2f} L"
    return f"{x} ml"

def csv_bytes_all():
    rows = read_data_rows()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "ml"])
    for d, m in rows:
        writer.writerow([d.isoformat(), m])
    return buf.getvalue().encode("utf-8")

# ----------------- SVG chart renderer (no libs) -----------------
def render_week_svg(week_data: list[tuple[date, int]], goal_ml: int = DAILY_GOAL_ML, width=900, height=280) -> str:
    """
    week_data: list of (date_obj, ml)
    Returns an HTML string containing an SVG bar chart.
    """
    labels = [d.strftime("%a %d") for d, _ in week_data]
    values = [v for _, v in week_data]
    max_val = max(max(values, default=0), goal_ml)
    # padding
    left_pad = 60
    right_pad = 20
    top_pad = 30
    bottom_pad = 60
    chart_w = width - left_pad - right_pad
    chart_h = height - top_pad - bottom_pad
    bar_w = chart_w / max(1, len(values)) * 0.6
    gap = chart_w / max(1, len(values)) * 0.4

    # normalize values to chart height
    def y_for(val):
        # inverted SVG Y
        if max_val == 0:
            return top_pad + chart_h
        return top_pad + (1 - (val / max_val)) * chart_h

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    # background
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="transparent"/>')
    # y axis labels (0, mid, max)
    for label_val, frac in [(0, 0.0), (max_val//2, 0.5), (max_val, 1.0)]:
        y = y_for(label_val)
        svg.append(f'<text x="{left_pad-10}" y="{y+4}" font-size="12" text-anchor="end" fill="#6b7280">{label_val if label_val>=1000 else label_val}</text>')
        # grid lines
        svg.append(f'<line x1="{left_pad}" y1="{y}" x2="{width-right_pad}" y2="{y}" stroke="#eee" stroke-dasharray="3 3" />')

    # goal line
    goal_y = y_for(goal_ml)
    svg.append(f'<line x1="{left_pad}" y1="{goal_y}" x2="{width-right_pad}" y2="{goal_y}" stroke="#ffd200" stroke-width="2" stroke-dasharray="6 4" />')
    svg.append(f'<text x="{width-right_pad}" y="{goal_y-6}" font-size="12" text-anchor="end" fill="#b36b00">Goal: {goal_ml//1000:.1f} L</text>')

    # bars
    for i, val in enumerate(values):
        x = left_pad + i * (bar_w + gap) + gap/2
        y = y_for(val)
        h = (top_pad + chart_h) - y
        color = "#2AA7A8" if val < goal_ml else "#0b845e"
        # bar rect
        svg.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" rx="6" fill="{color}"/>')
        # value label
        svg.append(f'<text x="{x + bar_w/2}" y="{y - 8}" font-size="12" text-anchor="middle" fill="#052a66" font-weight="700">{format_ml(val)}</text>')
        # x label
        svg.append(f'<text x="{x + bar_w/2}" y="{top_pad + chart_h + 18}" font-size="11" text-anchor="middle" fill="#6b7280">{html.escape(labels[i])}</text>')

    svg.append('</svg>')
    html_block = f'<div style="overflow:auto;">{ "".join(svg) }</div>'
    return html_block

# ----------------- Session defaults -----------------
if "feedback" not in st.session_state:
    st.session_state["feedback"] = ""

# ----------------- UI -----------------
left, right = st.columns([3, 1])
with left:
    st.markdown("<h1 style='margin:0'>Water Intake Tracker 💧</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6b7280; margin-top:6px;'>Log daily water (ml). Goal: <strong>3.0 L</strong>.</div>", unsafe_allow_html=True)
with right:
    if st.button("Clear all history"):
        clear_all_history()
        st.session_state["feedback"] = "All history cleared."

st.markdown("<hr/>", unsafe_allow_html=True)

col_main, col_side = st.columns([2.2, 1], gap="large")

with col_main:
    st.markdown("## Today")
    rows_all = read_data_rows()
    today_total = get_today_total(rows_all)
    pct = min(today_total / DAILY_GOAL_ML, 1.0)
    remaining = max(DAILY_GOAL_ML - today_total, 0)

    c1, c2 = st.columns([1.6, 1], gap="small")
    with c1:
        st.markdown(f"<div style='font-size:36px; font-weight:900; color:#052a66'>{format_ml(today_total)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#6b7280; font-weight:700'>Remaining: <strong>{format_ml(remaining)}</strong> to reach 3.0 L</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div style='width:120px; height:120px; margin:8px auto; position:relative;'>
              <div style='width:100%; height:100%; border-radius:50%; background:conic-gradient(#2AA7A8 {int(pct*360)}deg, #e6f6f5 {int(pct*360)}deg); display:flex; align-items:center; justify-content:center; box-shadow:0 8px 18px rgba(10,20,30,0.06);'>
                <div style='font-weight:900; color:#052a66'>{int(pct*100)}%</div>
              </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("**Quick add**")
    qb1, qb2, qb3, qb4 = st.columns(4)
    if qb1.button(" + 250 ml"):
        append_entry(date.today(), 250)
        st.session_state["feedback"] = "Added 250 ml."
    if qb2.button(" + 500 ml"):
        append_entry(date.today(), 500)
        st.session_state["feedback"] = "Added 500 ml."
    if qb3.button(" + 1000 ml"):
        append_entry(date.today(), 1000)
        st.session_state["feedback"] = "Added 1000 ml."
    if qb4.button(" + Glass (300 ml)"):
        append_entry(date.today(), 300)
        st.session_state["feedback"] = "Added 300 ml."

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    with st.form("manual_add"):
        st.markdown("**Manual add (ml)**")
        ml = st.number_input("ml", min_value=1, value=250, step=50, key="manual_ml")
        add_btn = st.form_submit_button("Add")
        clear_today = st.form_submit_button("Clear today's entries")
        if add_btn:
            append_entry(date.today(), int(ml))
            st.session_state["feedback"] = f"Added {int(ml)} ml."
        if clear_today:
            clear_today_entries()
            st.session_state["feedback"] = "Cleared today's entries."

    st.markdown("<hr/>", unsafe_allow_html=True)

    st.markdown("### Today's entries")
    rows_today = [r for r in rows_all if r[0] == date.today()]
    if not rows_today:
        st.info("No entries yet for today. Use quick add or manual add.")
    else:
        table_md = "<table style='width:320px; border-collapse:collapse'>"
        table_md += "<tr><th style='text-align:left; padding:6px 8px;'>#</th><th style='text-align:left; padding:6px 8px;'>ml</th></tr>"
        for idx, (_, m) in enumerate(rows_today, start=1):
            table_md += f"<tr><td style='padding:6px 8px; border-top:1px solid #eee'>{idx}</td><td style='padding:6px 8px; border-top:1px solid #eee'>{m} ml</td></tr>"
        table_md += "</table>"
        st.markdown(table_md, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    st.markdown("### Last 7 days")
    week = get_week_totals(rows=rows_all)
    svg_html = render_week_svg(week, goal_ml=DAILY_GOAL_ML, width=920, height=300)
    st.markdown(svg_html, unsafe_allow_html=True)

    # small label strip beneath (readable)
    labels_html = "<div style='display:flex; gap:12px; flex-wrap:wrap; margin-top:10px;'>"
    for d, v in week:
        labels_html += f"<div style='background:#f8fffe; padding:8px 10px; border-radius:8px;'><div style='font-weight:900; color:#052a66'>{format_ml(v)}</div><div style='color:#6b7280; font-weight:700'>{d.strftime('%a %d')}</div></div>"
    labels_html += "</div>"
    st.markdown(labels_html, unsafe_allow_html=True)

with col_side:
    st.markdown("## Stats & Export")
    week_total = sum(v for _, v in get_week_totals(rows=rows_all))
    st.markdown(f"<div style='color:#6b7280; font-weight:700'>This week total</div><div style='font-size:20px; font-weight:900; color:#052a66'>{format_ml(week_total)}</div>", unsafe_allow_html=True)

    if rows_all:
        csv_bytes = csv_bytes_all()
        st.download_button("Download full history (CSV)", data=csv_bytes, file_name="water_history.csv", mime="text/csv")
    else:
        st.markdown("<div style='color:#6b7280; font-weight:700'>No history to download yet.</div>", unsafe_allow_html=True)

    if st.button("Reset today"):
        clear_today_entries()
        st.session_state["feedback"] = "Today's entries cleared."

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("**Tips**")
    st.markdown("<ul><li>Use quick-add for speed.</li><li>3 L is a general guideline; adjust per your needs.</li></ul>", unsafe_allow_html=True)

# Show feedback message (persisted in session_state)
if st.session_state.get("feedback"):
    st.success(st.session_state["feedback"])
    st.session_state["feedback"] = ""
