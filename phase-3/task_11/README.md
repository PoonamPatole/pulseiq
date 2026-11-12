# Task 11 — P&L and expense analytics

Build the finance aggregates, then launch the dashboard from the project root:

```powershell
.\.venv\Scripts\python.exe .\phase-3\task_11\build_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\phase-3\task_11\app.py
```

The P&L uses active, non-group Profit & Loss accounts from the ledger. Revenue is accounts 4001–4004, displayed as positive; interest income account 4900 is shown separately. Net profit is revenue plus other income less expenses, and operating margin is net profit divided by revenue, matching governed metric definitions. Expenses are debit-normal. Group headings are excluded so a parent and its detail accounts are never counted together.

Expense category and vendor views use `fact_expense.amount_excl_gst`. They describe vendor bills only and do not equal all ledger expenses, which also include payroll, depreciation, and other non-bill entries. The monthly selector filters the P&L table, category view, and top-10 vendor view; the chart keeps the full monthly trend visible.

The workbook README headline section contains dataset counts, not monthly P&L totals. The tie-out compares the derived P&L with governed M16–M18 views. See `evidence/tieout.csv` and `evidence/findings.md` for the monthly comparison and analysis.
