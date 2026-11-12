"""Task 12: invoices, receivables, and cash flow."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"
st.set_page_config(page_title="Task 12 | Receivables and cash", layout="wide")
st.title("Task 12 | Invoices, receivables, and cash flow")
st.markdown("**Open invoice statuses:** SENT, OVERDUE, and PARTIALLY_PAID. DRAFT, PAID, and CANCELLED are excluded.")
st.caption("Ageing uses days past due at the dataset cutoff. The 90+ bucket means more than 90 days, keeping the buckets exclusive. Zero days past due is included in 0–30 days.")


@st.cache_data(ttl=60)
def read(sql):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql).df()


try:
    buckets = read("SELECT * FROM metrics.t12_ar_buckets ORDER BY sort_order")
    check = read("SELECT * FROM metrics.t12_bucket_check").iloc[0]
    cash = read("SELECT * FROM metrics.t12_cash_monthly ORDER BY month")
    overdue = read("SELECT * FROM metrics.t12_overdue_clients ORDER BY overdue_balance DESC")
    client_days = read("SELECT * FROM metrics.t12_client_days_to_pay ORDER BY average_days_to_pay DESC")
except Exception as exc:
    st.error(f"Build Task 12 metrics first: `python .\\phase-3\\task_12\\build_metrics.py`. {exc}")
    st.stop()

cols = st.columns(3)
cols[0].metric("Open receivables", f"₹{check.open_receivables:,.0f}")
cols[1].metric("Open invoices", f"{int(check.open_invoice_count):,}")
cols[2].metric("Bucket total difference", f"₹{check.difference:,.2f}")

st.subheader("Receivables ageing")
st.plotly_chart(px.bar(buckets, x="ageing_bucket", y="receivables", text_auto=".2s",
                       category_orders={"ageing_bucket": buckets.ageing_bucket.tolist()},
                       labels={"ageing_bucket": "Days past due", "receivables": "Open balance (INR)"}), width="stretch")
st.dataframe(buckets[["ageing_bucket", "invoice_count", "receivables"]], hide_index=True, width="stretch")
st.success(f"Bucket check: ₹{check.bucket_total:,.2f} across the four buckets equals open receivables of ₹{check.open_receivables:,.2f} (difference ₹{check.difference:,.2f}).")

st.subheader("Clients with the most overdue money")
st.dataframe(overdue, hide_index=True, width="stretch")
st.subheader("Average days to pay by client")
st.dataframe(client_days.assign(average_days_to_pay=client_days.average_days_to_pay.round(1),
                                maximum_days_to_pay=client_days.maximum_days_to_pay.round(1)),
             hide_index=True, width="stretch")

st.subheader("Cash received versus cash paid by month")
st.plotly_chart(px.bar(cash, x="month", y=["cash_in", "cash_out"], barmode="group",
                       labels={"value": "INR", "variable": "Cash movement", "month": "Month"}), width="stretch")
st.dataframe(cash, hide_index=True, width="stretch")
st.caption("Cash in is invoice payments by payment date. Cash out is expense bills with a paid date, using total amount including GST. Unpaid expense bills are not counted as cash out.")
st.info("A client paying at 75 days is a risk if that exceeds agreed terms or the exposure is concentrated. Ask Finance about contractual terms, overdue balance, disputes, promised payment dates, payment history, and the cash forecast impact.")
