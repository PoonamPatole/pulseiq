"""Task 7: actual exits and grouped attrition predictions."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DB=Path(__file__).resolve().parent.parent/"pulseiq.duckdb"
st.set_page_config(page_title="Task 7 | Attrition",layout="wide")
st.title("Task 7 | Attrition analytics")
st.caption("Actual exits and modelled risk are separate measures. No person-level risk is shown.")
@st.cache_data(ttl=60)
def read(sql):
    with duckdb.connect(str(DB),read_only=True) as c: return c.execute(sql).df()
try:
    actual=read("""SELECT h.month_start_date AS month,h.department_id,d.department_name,
      SUM(h.exits) AS exits,SUM(h.voluntary_exits) AS voluntary_exits,
      100.0*SUM(h.exits)/NULLIF(SUM(h.headcount_start),0) AS attrition_pct
      FROM warehouse.fact_headcount_monthly h LEFT JOIN warehouse.dim_department d USING(department_id)
      GROUP BY 1,2,3 ORDER BY 1,2""")
    risk=read("""SELECT r.department_id,d.department_name,r.as_of_date,
      COUNT(DISTINCT r.employee_id) AS scored_people,
      COUNT(DISTINCT r.employee_id) FILTER(WHERE upper(r.risk_band)='HIGH') AS high_risk,
      100.0*COUNT(DISTINCT r.employee_id) FILTER(WHERE upper(r.risk_band)='HIGH')/NULLIF(COUNT(DISTINCT r.employee_id),0) AS high_risk_pct
      FROM warehouse.fact_attrition_risk r LEFT JOIN warehouse.dim_department d USING(department_id)
      GROUP BY 1,2,3 HAVING COUNT(DISTINCT r.employee_id)>=5 ORDER BY 3,2""")
    tenure=read("""WITH exit_records AS (
      SELECT employee_id,department_id,hire_date,exit_date
      FROM warehouse.dim_employee
      WHERE exit_date IS NOT NULL AND hire_date IS NOT NULL
        AND exit_date BETWEEN valid_from AND COALESCE(valid_to,exit_date)
      )
      SELECT department_id,COUNT(*) AS exits,
        AVG(date_diff('day',hire_date,exit_date)/365.25) AS avg_tenure_years
      FROM exit_records
      GROUP BY 1 HAVING COUNT(*)>=5""")
except Exception as e: st.error(f"Build Tasks 1–4 first. {e}"); st.stop()
st.subheader("Actual exits")
st.plotly_chart(px.bar(actual,x="month",y="exits",color="department_name",barmode="group",title="Exits by month and department"),width="stretch")
st.dataframe(actual.sort_values("exits",ascending=False).head(10),hide_index=True,width="stretch")
st.caption("Voluntary exits are reported where supplied. Other exit reasons are not available in this monthly fact. Tenure is an aggregate of employee dimension exit dates; only groups of five or more are shown.")
st.subheader("Tenure at exit (grouped)")
if not tenure.empty: st.dataframe(tenure,hide_index=True,width="stretch")
st.subheader("Predicted, not certain")
st.warning("Risk is a model estimate for discussion, not a fact, diagnosis, or decision about an employee. Predictions can be wrong and must not be used alone for employment decisions.")
st.plotly_chart(px.bar(risk,x="department_name",y="high_risk_pct",color="as_of_date",barmode="group",title="High risk share by department (groups of at least 5)"),width="stretch")
st.dataframe(risk,hide_index=True,width="stretch")
st.subheader("Largest observations")
for _,r in actual.nlargest(3,"exits").iterrows(): st.write(f"{pd.Timestamp(r.month):%b %Y}, {r.department_name}: {int(r.exits)} exits ({r.attrition_pct:.2f}% of starting headcount).")
