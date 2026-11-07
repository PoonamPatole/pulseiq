"""Task 11: P&L and expense analytics."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "pulseiq.duckdb"
st.set_page_config(page_title="Task 11 | P&L and expenses", layout="wide")
st.title("Task 11 | Profit and loss and expense analytics")
st.caption("Ledger P&L uses active detail accounts only. Expense bills are shown GST-exclusive.")


@st.cache_data(ttl=60)
def read(sql, params=()):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql, list(params)).df()


try:
    pl = read("SELECT * FROM metrics.t11_pl_monthly ORDER BY month")
    categories = read("SELECT * FROM metrics.t11_expense_category ORDER BY month, expense_amount DESC")
    vendors = read("SELECT * FROM metrics.t11_vendor_spend ORDER BY month, expense_amount DESC")
    tieout = read("SELECT * FROM metrics.t11_tieout ORDER BY month")
except Exception as exc:
    st.error(f"Build Task 11 metrics first: `python .\\task_11\\build_metrics.py`. {exc}")
    st.stop()

months = sorted(pd.to_datetime(pl.month).dt.date.unique())
if not months:
    st.warning("No P&L months are available.")
    st.stop()
month = st.sidebar.selectbox("P&L month", months, format_func=lambda d: d.strftime("%b %Y"))
selected = pl[pd.to_datetime(pl.month).dt.date == month].iloc[0]
cols = st.columns(4)
values = [selected.revenue, selected.expenses, selected.net_profit, selected.operating_margin_pct]
labels = ["Revenue", "Expenses", "Net profit", "Operating margin"]
for col, label, value in zip(cols, labels, values):
    col.metric(label, f"{value:,.2f}%" if label == "Operating margin" else f"₹{value:,.0f}")

st.subheader("Monthly P&L")
st.plotly_chart(px.line(pl, x="month", y=["revenue", "expenses", "net_profit"], markers=True,
                        labels={"value": "INR", "variable": "P&L line", "month": "Month"}), width="stretch")
selected_pl = pl[pd.to_datetime(pl.month).dt.date == month].copy()
selected_pl["operating_margin_pct"] = selected_pl.operating_margin_pct.round(2)
st.dataframe(selected_pl, hide_index=True, width="stretch")

month_mask = pd.to_datetime(categories.month).dt.date == month
monthly_categories = categories[month_mask].sort_values("expense_amount", ascending=False)
month_mask = pd.to_datetime(vendors.month).dt.date == month
monthly_vendors = vendors[month_mask].nlargest(10, "expense_amount")
left, right = st.columns(2)
with left:
    st.subheader("Expense by category")
    st.plotly_chart(px.bar(monthly_categories, x="category", y="expense_amount",
                           title="Expense bills by category (excl. GST)",
                           labels={"expense_amount": "INR", "category": "Category"}), width="stretch")
with right:
    st.subheader("Top 10 vendors")
    st.plotly_chart(px.bar(monthly_vendors.sort_values("expense_amount"), x="expense_amount", y="vendor_name",
                           orientation="h", title="Vendor bills (excl. GST)",
                           labels={"expense_amount": "INR", "vendor_name": "Vendor"}), width="stretch")
st.dataframe(monthly_categories, hide_index=True, width="stretch")
st.dataframe(monthly_vendors, hide_index=True, width="stretch")

st.subheader("Monthly tie-out to governed metrics")
st.dataframe(tieout.round(2), hide_index=True, width="stretch")
st.caption("Revenue follows M16 (accounts 4001–4004); interest income 4900 is separate and included in net profit. Group headings are excluded. Expense bills are shown GST-exclusive and are not the full ledger expense total.")
st.info("The workbook README headline figures are dataset row counts, not P&L answer-key totals. This tie-out compares Task 11 with governed M16–M18 views; it does not claim to reconcile to a separate Finance answer key.")
