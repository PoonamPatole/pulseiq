"""Task 6: attendance and leave trends."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DB = Path(__file__).resolve().parent.parent / "pulseiq.duckdb"
st.set_page_config(page_title="Task 6 | Attendance", layout="wide")
st.title("Task 6 | Attendance and leave")
st.caption("Monthly rates use recorded scheduled workdays as the denominator.")

@st.cache_data(ttl=60)
def read(sql):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql).df()

try:
    data = read("""
      SELECT a.period_end_date AS month, a.department_id,
        d.department_name,
        SUM(a.present_days + 0.5*a.half_days_unpaid)/NULLIF(SUM(a.scheduled_days),0) AS attendance_rate,
        SUM(a.late_arrivals)::DOUBLE/NULLIF(SUM(a.present_days),0) AS late_arrivals_per_present_day,
        SUM(a.overtime_hours) AS overtime_hours,
        SUM(a.scheduled_days) AS scheduled_days,
        SUM(a.present_days) AS present_days
      FROM warehouse.fact_attendance_monthly a
      LEFT JOIN warehouse.dim_department d USING(department_id)
      GROUP BY 1,2,3 ORDER BY 1,2
    """)
    leave = read("""
      SELECT date_trunc('month', l.start_date)::DATE AS month,
        t.leave_type_name AS leave_type, SUM(l.days) AS leave_days
      FROM warehouse.fact_leave l LEFT JOIN warehouse.dim_leave_type t USING(leave_type_code)
      WHERE lower(l.status)='approved' GROUP BY 1,2 ORDER BY 1,2
    """)
    holidays = read("""
      SELECT month_start_date AS month, COUNT(*) FILTER (WHERE upper(is_holiday)='Y') AS holidays,
        COUNT(*) FILTER (WHERE upper(is_working_day)='Y') AS working_days
      FROM warehouse.dim_date GROUP BY 1 ORDER BY 1
    """)
except Exception as e:
    st.error(f"Build Tasks 1–4 first. {e}"); st.stop()

depts = sorted(data.department_name.dropna().unique())
sel = st.sidebar.selectbox("Department", ["All departments", *depts])
shown = data if sel == "All departments" else data[data.department_name == sel]
if shown.empty:
    st.info("No results for this department."); st.stop()
monthly = shown.groupby("month", as_index=False).agg(present_days=("present_days","sum"),scheduled_days=("scheduled_days","sum"),late_arrivals_per_present_day=("late_arrivals_per_present_day","mean"),overtime_hours=("overtime_hours","sum"))
monthly["attendance_rate"] = monthly.present_days / monthly.scheduled_days
left,right=st.columns(2)
left.plotly_chart(px.line(monthly,x="month",y="attendance_rate",markers=True,title="Attendance rate",labels={"attendance_rate":"Rate","month":"Month"}),use_container_width=True)
right.plotly_chart(px.line(monthly,x="month",y="overtime_hours",markers=True,title="Overtime hours",labels={"overtime_hours":"Hours","month":"Month"}),use_container_width=True)
st.plotly_chart(px.bar(shown,x="month",y="late_arrivals_per_present_day",color="department_name",barmode="group",title="Late arrivals per present day"),use_container_width=True)
leave_months=leave if sel=="All departments" else leave # leave requests have no department field
st.caption("Leave totals are company-wide because leave facts have no department key. Only approved leave is counted.")
st.plotly_chart(px.bar(leave_months,x="month",y="leave_days",color="leave_type",title="Approved leave days by type"),use_container_width=True)
st.subheader("Calendar context")
st.dataframe(holidays,hide_index=True,use_container_width=True)
st.info("Check months with holidays or fewer working days before interpreting a rate dip. A long weekend cannot be identified reliably from the supplied calendar alone.")
st.subheader("Three data observations")
for _,r in monthly.sort_values("attendance_rate").head(3).iterrows():
    st.write(f"{pd.Timestamp(r.month):%B %Y}: attendance was {r.attendance_rate:.1%}; {r.overtime_hours:,.1f} overtime hours were recorded. Calendar rows are shown above for context.")
