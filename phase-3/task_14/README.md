# Task 14 — AI signals dashboard

Build the Task 14 views and open the dashboard from the project root:

```powershell
.\.venv\Scripts\python.exe .\phase-3\task_14\build_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\phase-3\task_14\app.py
```

Anomaly exposures are grouped by `reason_code`; only rows with `flagged='Y'` are included. The anomaly contract says attendance rows do not have `money_at_risk`, so they are shown as unquantified rather than treated as zero exposure. The page shows the highest-exposure types first and labels model output for human review.

The forecast comparison uses company-level (`department_id='ALL'`) headcount and attrition forecasts to avoid adding company totals to department forecasts. Historical actuals are calculated from `fact_headcount_monthly`. Forecast error is absolute error divided by absolute actual, expressed as a percent. The current forecast periods begin in October 2026, while actuals end in September 2026, so current error is N/A until actuals are available. See `evidence/forecast_error.csv` and `evidence/forecast_notes.md`. The band is the supplied 80% lower-to-upper interval.
