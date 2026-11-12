"""Task 13: cross-department impact view."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"
st.set_page_config(page_title="Task 13 | Department impact", layout="wide")
st.title("Task 13 | Cross-department impact")
st.caption("Grain: one row per department and month. Each source is aggregated to this grain before joining.")


@st.cache_data(ttl=60)
def read(sql):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql).df()


try:
    data = read("SELECT * FROM metrics.t13_department_month ORDER BY month, department_id")
    recon = read("SELECT * FROM metrics.t13_reconciliation ORDER BY month, department_id, metric_name")
    summary = read("SELECT * FROM metrics.t13_reconciliation_summary")
    leave_quality = read("SELECT * FROM metrics.t13_leave_quality").iloc[0]
except Exception as exc:
    st.error(f"Build Task 13 metrics first: `python .\\phase-3\\task_13\\build_metrics.py`. {exc}")
    st.stop()

months = sorted(pd.to_datetime(data.month).dt.date.unique())
month = st.sidebar.selectbox("Month", months, index=len(months)-1,
                             format_func=lambda d: d.strftime("%b %Y"))
month_data = data[pd.to_datetime(data.month).dt.date == month].copy()

metric_checks = int(summary.metric_checks.sum()) if not summary.empty else 0
differences = int(summary.loc[summary.result == "DIFFERENCE", "metric_checks"].sum()) if not summary.empty else 0
left, right = st.columns(2)
left.metric("Reference checks", f"{metric_checks:,}")
right.metric("Outside rounding tolerance", f"{differences:,}")

st.subheader("Department comparison: cost, overtime and attrition")
chart_data = month_data.dropna(subset=["overtime_pay", "attrition_rate_monthly_pct", "employer_cost"])
chart_data = chart_data.sort_values("employer_cost", ascending=True)
departments = chart_data.department_name.tolist()
fig = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.12,
                    subplot_titles=("Employer cost (INR)", "Overtime cost (INR)", "Attrition (%)"))
series = [
    ("employer_cost", "Employer cost", "INR"),
    ("overtime_pay", "Overtime cost", "INR"),
    ("attrition_rate_monthly_pct", "Attrition", "%"),
]
for col, (field, label, unit) in enumerate(series, start=1):
    values = chart_data[field]
    text = [f"{value:,.1f}%" if unit == "%" else f"₹{value:,.0f}" for value in values]
    trace = go.Bar(x=values, y=departments, orientation="h", name=label,
                   text=text, textposition="outside", cliponaxis=False,
                   hovertemplate=f"%{{y}}<br>{label}: %{{x:,.2f}} {unit}<extra></extra>")
    if field == "attrition_rate_monthly_pct":
        trace.marker.color = "#7E57C2"
    fig.add_trace(trace, row=1, col=col)
    fig.update_xaxes(title_text=unit, row=1, col=col)
    fig.update_yaxes(categoryorder="array", categoryarray=departments, row=1, col=col)
fig.update_layout(title=f"Department comparison — {month:%b %Y}", showlegend=False,
                  height=560, margin=dict(l=170, r=35, t=100, b=55))
st.plotly_chart(fig, width="stretch")
st.caption("Each panel has its own scale. Co-movement does not establish that overtime causes attrition.")
st.info("Other explanations to check include understaffing or vacancies, seasonal workload, team or role mix, manager changes, tenure, leave patterns, and exit reasons. Compare trends over time and review these factors with Finance and HR before attributing cause.")

st.subheader("Combined department-month table")
visible = ["department_id", "department_name", "month", "headcount_end", "employer_cost",
           "overtime_pay", "overtime_hours", "attendance_rate", "approved_leave_days",
           "leave_days_per_head", "exits", "attrition_rate_monthly_pct", "cost_per_head",
           "overtime_share_pct"]
table = month_data[visible].copy()
numeric_columns = table.select_dtypes(include="number").columns
table[numeric_columns] = table[numeric_columns].round(3)
st.dataframe(table, hide_index=True, width="stretch")

st.subheader("PQ-13 reference differences for the selected month")
month_recon = recon[pd.to_datetime(recon.month).dt.date == month]
month_diff = month_recon[month_recon.result == "DIFFERENCE"]
if month_diff.empty:
    st.success("All compared measures for this month match the reference within rounding tolerance.")
else:
    st.dataframe(month_diff[["department_id", "department_name", "metric_name", "actual_value",
                             "reference_value", "difference", "tolerance"]].round(4),
                 hide_index=True, width="stretch")
with st.expander("All reference checks for the selected month"):
    comparison = month_recon[["department_id", "department_name", "metric_name", "actual_value",
                              "reference_value", "difference", "result"]].copy()
    comparison_numeric_columns = comparison.select_dtypes(include="number").columns
    comparison[comparison_numeric_columns] = comparison[comparison_numeric_columns].round(4)
    st.dataframe(comparison, hide_index=True, width="stretch")
st.caption("Reference task-count and task-completion fields are outside this four-source task. The reconciliation covers shared payroll, headcount, and attendance measures. Leave has no reference field and is reported separately.")

with st.expander("Join order and leave allocation"):
    st.write("Payroll, attendance, and headcount are each grouped to department and month first. Approved leave is joined to the employee dimension by employee_key, allocated across covered months by working-day share, and then grouped to department and month. The four aggregates are left-joined to a department-by-payroll-month spine.")
    st.write(f"Approved leave rows with an end date before the start date: {int(leave_quality.invalid_date_ranges)}. Their recorded leave days are assigned to the start month and retained; inspect the source before treating that allocation as final.")

st.subheader("Reconciliation detail")
all_differences = recon[recon.result == "DIFFERENCE"].copy()
diff_numeric_columns = all_differences.select_dtypes(include="number").columns
all_differences[diff_numeric_columns] = all_differences[diff_numeric_columns].round(4)
st.dataframe(all_differences, hide_index=True, width="stretch")
