"""Task 9: department payroll costs and monthly reconciliation."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"pulseiq.duckdb"
KEY=ROOT/"data/04_Validation_Vault/unlock_PQ-09_reconciliation_answer_key.csv"
st.set_page_config(page_title="Task 9 | Payroll",layout="wide")
st.title("Task 9 | Payroll cost and reconciliation")
st.caption("Department figures are aggregated totals and averages. No salary detail is displayed.")
@st.cache_data(ttl=60)
def read(sql,params=()):
 with duckdb.connect(str(DB),read_only=True) as c:return c.execute(sql,list(params)).df()
try:
 data=read("""SELECT g.month_end_date AS month,g.department_id,d.department_name,
   g.metric_value AS gross_pay,n.metric_value AS net_pay,e.metric_value AS employer_cost,
   h.metric_value AS cost_per_employee
   FROM metrics.m07_gross_pay g
   JOIN metrics.m08_net_pay n USING(month_end_date,department_id)
   JOIN metrics.m09_employer_payroll_cost e USING(month_end_date,department_id)
   JOIN metrics.m10_cost_per_head h USING(month_end_date,department_id)
   LEFT JOIN warehouse.dim_department d USING(department_id)
   GROUP BY 1,2,3,4,5,6,7 ORDER BY 1,2""")
except Exception as e: st.error(f"Build Tasks 1–4 first. {e}"); st.stop()
depts=sorted(data.department_name.dropna().unique())
sel=st.sidebar.selectbox("Department",["All reportable departments",*depts])
shown=data if sel=="All reportable departments" else data[data.department_name==sel]
monthly=shown.groupby("month",as_index=False)[["gross_pay","net_pay","employer_cost"]].sum()
st.plotly_chart(px.line(monthly,x="month",y=["gross_pay","net_pay","employer_cost"],markers=True,title="Monthly payroll totals (INR)"),width="stretch")
st.plotly_chart(px.bar(shown,x="month",y="employer_cost",color="department_name",barmode="group",title="Employer cost by department"),width="stretch")
st.subheader("Department totals and average cost")
st.dataframe(shown[["month","department_name","gross_pay","net_pay","employer_cost","cost_per_employee"]],hide_index=True,width="stretch")
st.warning("Payroll is provisional: the quality gate recorded duplicate employee/run rows, orphan employee IDs, and five payroll-to-ledger differences. Do not remove rows without a traceable rule and finance review.")
st.subheader("Monthly answer-key reconciliation")
try:
 key=pd.read_csv(KEY,parse_dates=["month"])
 payroll=read("SELECT date_trunc('month',period_end_date)::DATE AS month,SUM(employer_cost) AS payroll_employer_cost FROM warehouse.fact_payroll GROUP BY 1 ORDER BY 1")
 recon=payroll.merge(key[["month","payroll_employer_cost","ledger_salary_related_expense","payroll_vs_ledger_difference"]],on="month",suffixes=("_warehouse","_key"))
 recon["difference_vs_key"]=(recon.payroll_employer_cost_warehouse-recon.payroll_employer_cost_key).round(2)
 st.dataframe(recon,hide_index=True,width="stretch")
 st.caption("The answer key is company-level by month; it does not validate department allocations. The underlying quality findings remain visible and are not silently corrected.")
except Exception as e: st.error(f"Could not compare the supplied monthly answer key: {e}")
st.markdown("**Finance note:** We found duplicate and unmatched payroll records and flagged them for review. The monthly reconciliation also shows five differences, including the documented June 2026 variance. We are preserving the source rows while Finance confirms the correct adjustments. No employee salary is displayed here.")
