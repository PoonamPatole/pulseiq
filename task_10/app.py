"""Task 10: payroll budget variance and KPI targets."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"pulseiq.duckdb"
st.set_page_config(page_title="Task 10 | Budget and KPIs",layout="wide")
st.title("Task 10 | Budget versus actual and KPI targets")
st.markdown("**Sign rule:** variance = actual employer payroll cost − budget. Positive means overspend; negative means underspend.")
@st.cache_data(ttl=60)
def read(sql):
 with duckdb.connect(str(DB),read_only=True) as c:return c.execute(sql).df()
try:
 budget=read("SELECT * FROM metrics.t10_budget_variance ORDER BY month,department_id")
 score=read("SELECT * FROM metrics.t10_kpi_scorecard ORDER BY month,department_id")
except Exception as e: st.error(f"Run `python .\\task_10\\build_metrics.py` after Tasks 1–4. {e}"); st.stop()
depts=sorted(budget.department_name.dropna().unique())
sel=st.sidebar.selectbox("Department",["All reportable departments",*depts])
shown=budget if sel=="All reportable departments" else budget[budget.department_name==sel]
top=shown[shown.variance>0].groupby("department_name",as_index=False).variance.sum().sort_values("variance",ascending=False).head(10)
st.plotly_chart(px.bar(top,x="department_name",y="variance",title="Departments ranked by total overspend (INR)",labels={"variance":"Overspend (INR)"}),use_container_width=True)
st.subheader("Budget variance detail")
st.dataframe(shown,hide_index=True,use_container_width=True)
st.subheader("KPI scorecard")
visible=score if sel=="All reportable departments" else score[score.department_name==sel]
st.dataframe(visible,hide_index=True,use_container_width=True)
st.caption("Green means the observed KPI meets its supplied target; red means it misses; no data is not scored. Budget overspend is ranked separately. A missing budget refresh after a hiring freeze should be noted beside the variance and discussed with Finance.")
st.subheader("Top two overspend recommendations")
for _,r in top.head(2).iterrows():
 st.write(f"{r.department_name}: review hiring, vacancies and payroll changes against the approved plan; cumulative overspend is INR {r.variance:,.0f}. Confirm whether the plan reflects the hiring-freeze date before changing staffing.")
st.subheader("Three manual checks")
st.info("Choose three department-month rows and verify actual, budget, actual − budget, and percentage = variance ÷ budget × 100. Record the results in evidence/verification.md.")
