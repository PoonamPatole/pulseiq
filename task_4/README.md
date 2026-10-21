# Task 4 — Governed metric layer

Run from the project root after Tasks 1 and 2 have built the DuckDB database:

```powershell
.\.venv\Scripts\python.exe .\task_4\create_metric_views.py
```

This creates reusable views for the 28 supplied metrics plus M29, along with supporting aggregate views, in the `metrics` schema and `metrics.metric_catalog` in the project-root `pulseiq.duckdb`. Each metric view includes its date/team/department/account grouping columns and `metric_value`; the helper `group_size` is used to filter small groups and is not exposed in the final view.

Examples to inspect in DuckDB:

```sql
SELECT * FROM metrics.metric_catalog ORDER BY metric_id;
SELECT * FROM metrics.m01_headcount ORDER BY month_start_date, department_id;
SELECT * FROM metrics.m28_forecast_error_mape ORDER BY month_start_date;
```

The M28 view currently returns forecast records with `metric_value = NULL` and `data_status = 'NO_ACTUALS_YET'`: forecasts are for months after the supplied actual headcount ends. It does not invent an error value.

See [metric decisions](docs/metric_decisions.md) and [hand checks](docs/hand_checks.md) for formula choices, privacy thresholds, and the five source-to-view comparisons.

M29, month-over-month headcount growth, was added for the Phase 1 mini-challenge. Its definition and calculator check are in `task_5/docs/mini_challenge.md`.

## Data quality caveat

The metric views are reusable definitions over Task 2's warehouse. Some source facts still have critical Task 3 failures (including payroll-to-ledger differences and duplicate payroll rows). The metric definitions run, but payroll-derived results should be treated as provisional until those source issues are resolved and the quality gate passes.
