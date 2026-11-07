"""Task 15: executive company-health scorecard."""
from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "pulseiq.duckdb"
DETAIL_PAGE = "pages/02_KPI_Detail.py"

st.set_page_config(page_title="Task 15 | Executive scorecard", layout="wide")

st.markdown("""
<style>
@page { size: A4 landscape; margin: 8mm; }
@media print {
  header, [data-testid="stHeader"], [data-testid="stSidebar"],
  [data-testid="stToolbar"], [data-testid="stDecoration"], footer { display:none !important; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  h1 { font-size: 21pt !important; margin: 0 0 4mm !important; }
  [data-testid="stHorizontalBlock"] { gap: 3mm !important; }
  [data-testid="stVerticalBlock"] { gap: 2mm !important; }
  .kpi-card { min-height: 31mm !important; padding: 3mm !important; break-inside: avoid; }
  .kpi-value { font-size: 18pt !important; }
  .kpi-reason, .kpi-meta { font-size: 8pt !important; }
  a { color: #111 !important; }
}
.kpi-card { color:#1F2937; border:1px solid rgba(128,128,128,.35); border-radius:10px; padding:14px 15px; min-height:160px; }
.kpi-name { font-size:15px; font-weight:650; margin-bottom:3px; }
.kpi-value { font-size:27px; font-weight:700; margin:5px 0; }
.kpi-meta { font-size:12px; opacity:.82; line-height:1.5; }
.kpi-reason { font-size:12px; opacity:.8; line-height:1.3; margin-top:6px; }
.status { font-weight:700; font-size:12px; }
</style>
""", unsafe_allow_html=True)

st.title("Executive company-health scorecard")

@st.cache_data(ttl=60)
def read_scorecard():
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute("SELECT * FROM metrics.t15_scorecard ORDER BY month, metric_id").df()

try:
    scorecard = read_scorecard()
except Exception as exc:
    st.error(f"Build Task 15 metrics first: `python .\\task_15\\build_metrics.py`. {exc}")
    st.stop()

if scorecard.empty:
    st.warning("No scorecard metrics are available.")
    st.stop()

months = sorted(pd.to_datetime(scorecard.month).dropna().unique())
selected = st.sidebar.selectbox("Scorecard month", months, index=len(months)-1,
                                format_func=lambda value: pd.Timestamp(value).strftime("%b %Y"))
current = scorecard[pd.to_datetime(scorecard.month) == pd.Timestamp(selected)].copy()

KPI_INFO = {
    "M01": ("Company headcount", "people", "A founder needs the workforce size to understand operating capacity.", "#2563EB", "0"),
    "M16": ("Revenue", "currency", "Revenue shows the scale of sales activity in the selected month.", "#2563EB", "0"),
    "M17": ("Net profit", "currency", "Net profit shows what remains after the costs included in the governed P&L.", "#2563EB", "0"),
    "M18": ("Operating margin", "percent", "Operating margin shows how much of revenue remains as operating profit.", "#2563EB", "2"),
    "M04": ("Monthly attrition", "percent", "Attrition signals whether the company is retaining its workforce.", "#B42318", "2"),
    "M13": ("Attendance rate", "percent", "Attendance indicates whether scheduled staff capacity is present.", "#067647", "1"),
    "M11": ("Overtime share", "percent", "Overtime share helps reveal workload pressure and additional payroll exposure.", "#B54708", "1"),
    "M22": ("Task completion", "percent", "Task completion gives a view of delivery progress against planned work.", "#067647", "1"),
}

def formatted_value(row, key):
    value = row[key]
    if pd.isna(value):
        return "N/A"
    name, unit, *_ = KPI_INFO[row.metric_id]
    if unit == "currency":
        return f"₹{value:,.0f}"
    if unit == "percent":
        return f"{value:.{int(KPI_INFO[row.metric_id][4])}f}%"
    return f"{value:,.0f} people"

def trend_text(row):
    delta = row.month_delta
    if pd.isna(delta):
        return "Trend: first available month"
    _, unit, *_ = KPI_INFO[row.metric_id]
    if unit == "currency":
        suffix = f" ({row.month_change_pct:+.1f}% MoM)" if pd.notna(row.month_change_pct) else ""
        return f"Trend: {delta:+,.0f}{suffix}"
    if unit == "percent":
        return f"Trend: {delta:+.2f} pp"
    return f"Trend: {delta:+,.0f} people"

st.caption(f"Month: {pd.Timestamp(selected).strftime('%B %Y')} · Values come from governed metric views. Four metrics have no numeric target in kpi_targets; no targets have been invented.")

for start in (0, 4):
    cols = st.columns(4, gap="small")
    for col, (_, row) in zip(cols, current.iloc[start:start+4].iterrows()):
        label, unit, reason, color, precision = KPI_INFO[row.metric_id]
        target = formatted_value(row, "target_value") if pd.notna(row.target_value) else "No target set"
        status = row.status
        bg = {"ON TARGET": "#E7F5EC", "NEEDS ATTENTION": "#FCE8E6", "NO TARGET": "#EEF2F6", "NO DATA": "#F2F4F7"}.get(status, "#EEF2F6")
        fg = {"ON TARGET": "#067647", "NEEDS ATTENTION": "#B42318", "NO TARGET": "#475467", "NO DATA": "#475467"}.get(status, "#475467")
        with col:
            st.markdown(
                f'<div class="kpi-card" style="background:{bg}">'
                f'<div class="kpi-name">{label}</div>'
                f'<div class="kpi-value">{formatted_value(row, "metric_value")}</div>'
                f'<div class="kpi-meta">Target: {target} · <span class="status" style="color:{fg}">{status}</span><br>{trend_text(row)}</div>'
                f'<div class="kpi-reason">{reason}</div></div>', unsafe_allow_html=True)
            st.page_link(DETAIL_PAGE, label="Metric details and source", icon="↗",
                         query_params={"metric": row.metric_id, "month": pd.Timestamp(selected).strftime("%Y-%m-%d")})

st.caption("Status follows the supplied target direction: lower is better for attrition and overtime; higher is better for attendance and task completion. Other KPIs remain unscored because no target was supplied.")
