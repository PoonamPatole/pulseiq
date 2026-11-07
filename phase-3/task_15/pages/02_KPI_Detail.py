"""Traceability page for an executive scorecard KPI."""
from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"
st.set_page_config(page_title="Task 15 | KPI detail", layout="wide")

@st.cache_data(ttl=60)
def read(sql, params=None):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql, params or []).df()

metric_id = st.query_params.get("metric", "M01")
month_arg = st.query_params.get("month")
try:
    details = read("""
        SELECT s.*
        FROM metrics.t15_scorecard s
        WHERE s.metric_id = ?
        ORDER BY s.month
    """, [metric_id])
except Exception as exc:
    st.error(f"Build Task 15 metrics first: `python .\\task_15\\build_metrics.py`. {exc}")
    st.stop()

if details.empty:
    st.error(f"No scorecard detail found for {metric_id}.")
    st.stop()

selected = details.iloc[-1]
if month_arg:
    matching = details[pd.to_datetime(details.month).dt.strftime("%Y-%m-%d") == month_arg]
    if not matching.empty:
        selected = matching.iloc[0]

st.title(f"{selected.metric_name} · KPI detail")
st.caption(f"{selected.metric_id} · Selected month: {pd.Timestamp(selected.month).strftime('%B %Y')}")
st.page_link("app.py", label="Back to executive scorecard", icon="←")

left, right = st.columns(2)
with left:
    st.metric("Selected value", f"{selected.metric_value:,.2f}" if pd.notna(selected.metric_value) else "N/A")
    st.metric("Supplied target", f"{selected.target_value:,.2f}" if pd.notna(selected.target_value) else "No target set")
    st.write(f"**Status:** {selected.status}")
with right:
    st.write(f"**Governed metric view:** `{selected.source_view}`")
    st.write(f"**Formula:** `{selected.formula}`")
    st.write(f"**Source table:** `{selected.source_table}`")
    st.write(f"**Metric grain:** {selected.grain}")

st.subheader("Monthly metric history")
history = details[["month", "metric_value", "target_value", "month_delta", "month_change_pct", "status", "source_view"]].copy()
history["month"] = pd.to_datetime(history.month).dt.strftime("%b %Y")
history = history.rename(columns={"month": "Month", "metric_value": "Value", "target_value": "Target",
                                  "month_delta": "Change from prior month", "month_change_pct": "MoM change %",
                                  "status": "Status", "source_view": "Metric view source"})
st.dataframe(history, hide_index=True, width="stretch")
