# Task 9 — Payroll cost and reconciliation

Run: `..\.venv\Scripts\python.exe -m streamlit run .\task_9\app.py`.

Gross, net, employer cost and cost per employee use governed M07–M10 views, which suppress groups below the metric threshold. The monthly reconciliation uses the supplied PQ-09 company-level answer key and displays the variance to that key. It does not claim that company totals prove department allocation accuracy.

Treat payroll figures as provisional pending Finance review. The quality findings documented by Task 3 include duplicate payroll employee/run rows, unmatched employee IDs, and five month differences. This app preserves rows and reports the known issues instead of assuming which pay rows are erroneous. Finance must confirm any row-level correction before excluding it. The key's company-level scope limits department-level reconciliation.
