"""Task 14: AI anomaly signals and forecasts."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"
st.set_page_config(page_title="Task 14 | AI signals", layout="wide")
st.title("Task 14 | AI signals")
st.caption("Model outputs are estimates for human review, not verified facts or decisions.")


@st.cache_data(ttl=60)
def read(sql):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql).df()


try:
    anomalies = read("SELECT * FROM metrics.t14_anomalies_by_type ORDER BY money_at_risk DESC NULLS LAST")
    forecasts = read("SELECT * FROM metrics.t14_forecast_accuracy ORDER BY metric, month")
    actuals = read("SELECT * FROM metrics.t14_actuals ORDER BY metric, month")
except Exception as exc:
    st.error(f"Build Task 14 metrics first: `python .\\phase-3\\task_14\\build_metrics.py`. {exc}")
    st.stop()

st.subheader("Flagged anomalies by type and estimated money at risk")
quantified = anomalies[anomalies.money_at_risk.notna()].sort_values("money_at_risk", ascending=True)
fig = go.Figure(go.Bar(x=quantified.money_at_risk, y=quantified.reason_label,
                       orientation="h", text=[f"₹{x:,.0f}" for x in quantified.money_at_risk],
                       textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}<br>Estimated money at risk: ₹%{x:,.2f}<extra></extra>"))
fig.update_layout(title="AI-generated, for human review — flagged payroll anomaly exposure",
                  xaxis_title="Estimated money at risk (INR)", yaxis_title="Anomaly type",
                  height=max(480, 34*len(quantified)+160), margin=dict(l=210,r=100,t=80,b=55))
st.plotly_chart(fig, width="stretch")
st.info("The model-estimated payroll exposures are grouped by reason code and ranked from largest to smallest. Attendance anomalies have no money estimate in the source contract; they are shown as unquantified below. Money at risk is potential exposure, not confirmed loss.")
st.dataframe(anomalies[["source_dataset", "reason_label", "reason_code", "anomaly_count",
                        "quantified_count", "money_at_risk", "highest_anomaly_score"]].assign(
                            money_at_risk=anomalies.money_at_risk.round(2)),
             hide_index=True, width="stretch")

st.subheader("Forecast versus actual with 80% confidence band")
metric_labels = {"headcount_end": "Company headcount", "attrition_rate_monthly_pct": "Monthly attrition rate (%)"}
available_metrics = [m for m in metric_labels if m in forecasts.metric.unique()]
selected_metric = st.selectbox("Forecast metric", available_metrics,
                               format_func=lambda value: metric_labels[value])
forecast = forecasts[forecasts.metric == selected_metric].sort_values("month")
history = actuals[actuals.metric == selected_metric].sort_values("month")
unit = "people" if selected_metric == "headcount_end" else "%"
chart = go.Figure()
chart.add_trace(go.Scatter(x=history.month, y=history.actual_value, mode="lines+markers",
                           name="Actual", line=dict(color="#2563EB", width=2),
                           hovertemplate="%{x|%b %Y}<br>Actual: %{y:.2f}<extra></extra>"))
chart.add_trace(go.Scatter(x=forecast.month, y=forecast.lower_80, mode="lines",
                           name="80% lower bound", line=dict(width=0), showlegend=False,
                           hoverinfo="skip"))
chart.add_trace(go.Scatter(x=forecast.month, y=forecast.upper_80, mode="lines",
                           name="80% confidence band", line=dict(width=0),
                           fill="tonexty", fillcolor="rgba(126,87,194,0.20)",
                           hovertemplate="%{x|%b %Y}<br>Upper bound: %{y:.2f}<extra></extra>"))
chart.add_trace(go.Scatter(x=forecast.month, y=forecast.forecast_value, mode="lines+markers",
                           name="AI forecast", line=dict(color="#7E57C2", width=2, dash="dash"),
                           hovertemplate="%{x|%b %Y}<br>Forecast: %{y:.2f}<extra></extra>"))
chart.update_layout(title="AI-generated, for human review — forecast and actuals",
                    xaxis_title="Month", yaxis_title=unit, hovermode="x unified",
                    legend_title="Series")
st.plotly_chart(chart, width="stretch")
st.info("The solid line is observed history. The dashed line is the point forecast; the shaded band is the model’s 80% range. The forecast is not a promise. A 12% error cannot be judged without the metric, horizon, baseline, business tolerance, and the cost of over- versus under-forecasting.")

st.subheader("Forecast error where actuals are available")
error_table = forecasts[["metric", "month", "forecast_value", "lower_80", "upper_80",
                         "actual_value", "absolute_error", "absolute_percentage_error", "actual_status"]].copy()
numeric = error_table.select_dtypes(include="number").columns
error_table[numeric] = error_table[numeric].round(2)
known = int(forecasts.actual_value.notna().sum())
if known == 0:
    st.warning("No forecast month has an actual value yet. Forecast errors and MAPE are N/A until actuals arrive; the table shows each month awaiting comparison.")
else:
    st.success(f"Forecast errors are calculated for {known} forecast month(s) with actuals.")
st.dataframe(error_table, hide_index=True, width="stretch")
