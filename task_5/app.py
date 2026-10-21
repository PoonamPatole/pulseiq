"""PulseIQ workforce and headcount dashboard (Task 5)."""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"
NAVY = "#1F4E79"  # headcount and workforce size
TEAL = "#2A9D8F"  # workforce composition

st.set_page_config(page_title="PulseIQ | Workforce", page_icon="◼", layout="wide")


@st.cache_data(ttl=60)
def read_metric(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Read-only query helper. Dashboard queries use metrics views only."""
    if not DB_FILE.exists():
        raise FileNotFoundError(f"DuckDB file not found: {DB_FILE}")
    con = duckdb.connect(str(DB_FILE), read_only=True)
    try:
        return con.execute(sql, list(params)).df()
    finally:
        con.close()


st.title("PulseIQ | Workforce and headcount")
st.caption("A monthly workforce snapshot built from the governed metric layer.")

try:
    department_frame = read_metric("""
        SELECT DISTINCT department_id, department_name
        FROM metrics.m01_department_headcount
        ORDER BY department_name
    """)
    available_months = read_metric("""
        SELECT DISTINCT month_start_date
        FROM metrics.m01_company_headcount
        ORDER BY month_start_date
    """)
    if department_frame.empty or available_months.empty:
        st.error("No reportable workforce metrics are available. Build the Task 4 and Task 5 metric views first.")
        st.stop()
except Exception as exc:
    st.error(f"Could not read workforce metric views: {exc}")
    st.info("From the project root, run the Task 4 metric builder and then `python .\\task_5\\build_workforce_metrics.py`.")
    st.stop()

months = pd.to_datetime(available_months["month_start_date"]).dt.date.tolist()
default_start_index = max(0, len(months) - 12)
default_range = (months[default_start_index], months[-1])
dept_labels = dict(zip(department_frame["department_id"], department_frame["department_name"]))

with st.sidebar:
    st.header("Filters")
    department_options = ["All reportable departments", *department_frame["department_id"].tolist()]
    selected_department = st.selectbox(
        "Department",
        options=department_options,
        format_func=lambda value: "All reportable departments" if value == "All reportable departments" else dept_labels.get(value, value),
        help="Small department groups are suppressed by the metric layer.",
    )
    date_range = st.date_input(
        "Month range",
        value=default_range,
        min_value=months[0],
        max_value=months[-1],
    )

if not isinstance(date_range, tuple) or len(date_range) != 2:
    st.info("Choose both a start month and an end month.")
    st.stop()

start_date, end_date = date_range
if start_date > end_date:
    st.error("Start month must be before end month.")
    st.stop()
all_departments_selected = selected_department == "All reportable departments"

# Use the safe company total when all reportable departments are selected.
# A department subset uses the privacy-filtered department metric view.
if all_departments_selected:
    trend = read_metric("""
        SELECT month_start_date, metric_value AS headcount
        FROM metrics.m01_company_headcount
        WHERE month_start_date BETWEEN ? AND ?
        ORDER BY month_start_date
    """, (start_date, end_date))
else:
    trend = read_metric(f"""
        SELECT month_start_date, metric_value AS headcount
        FROM metrics.m01_department_headcount
        WHERE month_start_date BETWEEN ? AND ?
          AND department_id = ?
        ORDER BY month_start_date
    """, (start_date, end_date, selected_department))

if trend.empty:
    st.warning("No headcount results for those filters.")
    st.stop()

trend["month_start_date"] = pd.to_datetime(trend["month_start_date"])
latest_date = trend["month_start_date"].max()
first_value = float(trend.iloc[0]["headcount"])
latest_value = float(trend.iloc[-1]["headcount"])
net_change = latest_value - first_value
change_pct = 100.0 * net_change / first_value if first_value else None
avg_headcount = float(trend["headcount"].mean())
if all_departments_selected:
    growth_row = read_metric("""
        SELECT metric_value FROM metrics.m29_headcount_growth_mom
        WHERE scope = 'Company' AND month_start_date = ?
    """, (latest_date.date(),))
else:
    growth_row = read_metric("""
        SELECT metric_value FROM metrics.m29_headcount_growth_mom
        WHERE scope = 'Department' AND department_id = ? AND month_start_date = ?
    """, (selected_department, latest_date.date()))
mom_growth = None if growth_row.empty else float(growth_row.iloc[0]["metric_value"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Headcount at period end", f"{latest_value:,.0f}")
col2.metric(
    "Change over selected period",
    f"{net_change:+,.0f}",
    delta=f"{change_pct:+.1f}%" if change_pct is not None else None,
)
col3.metric("Average monthly headcount", f"{avg_headcount:,.1f}")
col4.metric(
    "M29 | Month-over-month growth",
    f"{mom_growth:+.2f}%" if mom_growth is not None else "N/A",
    help="100 × (this month's headcount − previous month's headcount) ÷ previous month's headcount.",
)

department_clause = "" if all_departments_selected else "AND department_id = ?"
dept_params = () if all_departments_selected else (selected_department,)
department_data = read_metric(f"""
    SELECT department_id, department_name, metric_value AS headcount
    FROM metrics.m01_department_headcount
    WHERE month_start_date = ? {department_clause}
    ORDER BY headcount DESC
""", (latest_date.date(), *dept_params))

tier_data = read_metric(f"""
    SELECT category AS city_tier, SUM(metric_value) AS headcount
    FROM metrics.m01_headcount_by_location_tier
    WHERE month_start_date = ? {department_clause}
    GROUP BY category ORDER BY headcount DESC
""", (latest_date.date(), *dept_params))

mode_data = read_metric(f"""
    SELECT category AS work_mode, SUM(metric_value) AS headcount
    FROM metrics.m01_headcount_by_work_mode
    WHERE month_start_date = ? {department_clause}
    GROUP BY category ORDER BY headcount DESC
""", (latest_date.date(), *dept_params))

period_label = f"{start_date:%b %Y}–{end_date:%b %Y}"
scope_label = "all departments" if all_departments_selected else dept_labels.get(selected_department, selected_department)

st.subheader("Workforce trend")
trend_change_phrase = (
    f"grew by {net_change:,.0f} ({change_pct:+.1f}%)"
    if net_change > 0 and change_pct is not None
    else f"fell by {abs(net_change):,.0f} ({change_pct:.1f}%)"
    if net_change < 0 and change_pct is not None
    else "was unchanged"
)
fig_trend = px.line(
    trend, x="month_start_date", y="headcount", markers=True,
    title=f"Headcount {trend_change_phrase} across {period_label}",
    labels={"month_start_date": "Month", "headcount": "Employees"},
)
fig_trend.update_traces(line_color=NAVY, marker_color=NAVY)
fig_trend.update_layout(showlegend=False, margin=dict(l=10, r=10, t=65, b=10))
st.plotly_chart(fig_trend, use_container_width=True)
st.caption(
    f"{scope_label}: headcount moved from {first_value:,.0f} to {latest_value:,.0f} over the selected period."
)

left, right = st.columns(2)
with left:
    if not department_data.empty:
        top_department = department_data.iloc[0]
        st.subheader("Department mix")
        fig_department = px.bar(
            department_data, x="department_name", y="headcount",
            title=f"{top_department['department_name']} is largest with {top_department['headcount']:,.0f} employees",
            labels={"department_name": "Department", "headcount": "Employees"},
            color_discrete_sequence=[NAVY],
        )
        fig_department.update_layout(showlegend=False, margin=dict(l=10, r=10, t=65, b=10))
        fig_department.update_xaxes(tickangle=-25)
        st.plotly_chart(fig_department, use_container_width=True)
        st.caption(
            f"At {latest_date:%B %Y}, {top_department['department_name']} has the largest reportable department headcount."
        )
    else:
        st.info("No department groups meet the privacy threshold for this period.")

with right:
    if not tier_data.empty:
        top_tier = tier_data.iloc[0]
        tier_total = float(tier_data["headcount"].sum())
        tier_share = 100.0 * float(top_tier["headcount"]) / tier_total if tier_total else 0
        st.subheader("Department mix by location tier")
        fig_tier = px.bar(
            tier_data, x="city_tier", y="headcount",
            title=f"{top_tier['city_tier']} has the largest visible share ({tier_share:.1f}%)",
            labels={"city_tier": "City tier", "headcount": "Employees"},
            color_discrete_sequence=[TEAL],
        )
        fig_tier.update_layout(showlegend=False, margin=dict(l=10, r=10, t=65, b=10))
        st.plotly_chart(fig_tier, use_container_width=True)
        st.caption(
            f"{top_tier['city_tier']} accounts for {top_tier['headcount']:,.0f} of {tier_total:,.0f} employees in visible location groups."
        )
    else:
        st.info("No location-tier groups meet the privacy threshold for this period.")

if not mode_data.empty:
    top_mode = mode_data.iloc[0]
    mode_total = float(mode_data["headcount"].sum())
    mode_share = 100.0 * float(top_mode["headcount"]) / mode_total if mode_total else 0
    st.subheader("Work mode mix")
    fig_mode = px.bar(
        mode_data, x="work_mode", y="headcount",
        title=f"{top_mode['work_mode']} is the most common visible work mode ({mode_share:.1f}%)",
        labels={"work_mode": "Work mode", "headcount": "Employees"},
        color_discrete_sequence=[TEAL],
    )
    fig_mode.update_layout(showlegend=False, margin=dict(l=10, r=10, t=65, b=10))
    st.plotly_chart(fig_mode, use_container_width=True)
    st.caption(
        f"{top_mode['work_mode']} represents {top_mode['headcount']:,.0f} of {mode_total:,.0f} employees across visible work-mode groups."
    )
else:
    st.info("No work-mode groups meet the privacy threshold for this period.")

st.caption("Colour key: navy = workforce size; teal = workforce composition. Groups below the metric privacy threshold are suppressed.")
