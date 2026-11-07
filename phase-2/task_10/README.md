# Task 10 — Budget and KPI targets

First run `..\.venv\Scripts\python.exe .\task_10\build_metrics.py`, then run `..\.venv\Scripts\python.exe -m streamlit run .\task_10\app.py`.

The builder copies the supplied raw budget and targets into the warehouse and creates aggregated metric views. Positive budget variance means overspend; percentage variance is variance divided by budget. Department actuals are shown only for groups of at least five employees.

KPI status rules follow the supplied targets: attendance and task completion meet target when greater than or equal; overtime share and attrition meet target when less than or equal. A missing value is labelled No data. Task completion is averaged across teams in each department-month. Review whether the budget was updated after a hiring freeze before recommending staffing changes.
