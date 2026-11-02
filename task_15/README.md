# Task 15 — Executive company-health scorecard

From the project root, build the governed scorecard view and launch the page:

```powershell
.\.venv\Scripts\python.exe .\task_15\build_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\task_15\app.py
```

Choose a month in the sidebar. Each KPI links to a detail page with its metric-view source, dictionary formula and monthly history. Use the browser print command (Ctrl+P) and choose A4 landscape; print styles hide the sidebar and Streamlit controls.

The scorecard uses only governed metric views for actual values and `warehouse.kpi_targets` for goals. The supplied targets cover attrition, attendance, overtime share and task completion. Headcount, revenue, net profit and operating margin have no supplied target, so their status is `NO TARGET`.

For department-level rates, the company scorecard uses the average of reportable department rates for attrition and attendance. Overtime share is weighted by department employer payroll cost because target limits differ between departments. Task completion is averaged across departments with a reported value. The detail page links back to the source metric view and formula for review.

See [evidence/kpi_selection.md](evidence/kpi_selection.md) for the KPI rationale and the requested five-KPI choice.
