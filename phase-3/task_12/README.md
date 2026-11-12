# Task 12 — Invoices, receivables, and cash flow

Build the Task 12 views, then start the dashboard from the project root:

```powershell
.\.venv\Scripts\python.exe .\phase-3\task_12\build_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\phase-3\task_12\app.py
```

Open statuses are SENT, OVERDUE, and PARTIALLY_PAID. Receivable balances are aged using days past due at the dataset cutoff. The mutually exclusive buckets are 0–30, 31–60, 61–90, and more than 90 days; zero days past due falls into 0–30. Average days to pay uses paid invoices with a populated `days_to_pay` value.

Cash in is invoice-payment amount by payment date. Cash out is the total expense-bill amount by paid date, including GST. Only expenses with a paid date are counted as cash out.
