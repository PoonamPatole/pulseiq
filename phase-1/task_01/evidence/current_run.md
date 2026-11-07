# Task 1 current pipeline evidence

Run date: 2026-10-19. Source: CSV files under `data/03_Data/csv`; database: project-root `pulseiq.duckdb`.

## Facts checked against supplied detailed contracts and dictionary schemas

| Fact | Rows in | Passed | Quarantined | Status |
|---|---:|---:|---:|---|
| `fact_anomaly` | 405 | 405 | 0 | Detailed contract + dictionary type/nullability |
| `fact_attrition_risk` | 430 | 430 | 0 | Detailed contract + dictionary type/nullability |
| `fact_forecast` | 72 | 72 | 0 | Detailed contract + dictionary type/nullability |
| `fact_task` | 28,868 | 28,848 | 20 | Detailed contract + dictionary type/nullability |

## Facts checked against dictionary schema only

The supplied `data_contracts` sheet does not define allowed-value or business-rule contracts for these eight facts. The pipeline checks every column's dictionary-declared type and nullability; it does not invent allowed-value lists.

| Fact | Rows in | Passed | Quarantined | Status |
|---|---:|---:|---:|---|
| `fact_attendance_monthly` | 7,343 | 7,343 | 0 | Dictionary schema validated |
| `fact_expense` | 501 | 501 | 0 | Dictionary schema validated |
| `fact_headcount_monthly` | 891 | 891 | 0 | Dictionary schema validated |
| `fact_invoice` | 743 | 743 | 0 | Dictionary schema validated |
| `fact_invoice_payment` | 709 | 709 | 0 | Dictionary schema validated |
| `fact_leave` | 3,441 | 3,441 | 0 | Dictionary schema validated |
| `fact_ledger` | 6,784 | 6,784 | 0 | Dictionary schema validated |
| `fact_payroll` | 7,344 | 7,344 | 0 | Dictionary schema validated |

## Checks and rerun behavior

- CSV-to-raw reconciliation: 29 of 29 CSV files matched; 0 mismatches.
- `verify_rerun.py`: the raw, clean, summary, and quarantine tables had identical row counts and contents across two consecutive runs.
- The ETL command returns exit code 1 after loading because the Task 3 gate finds five Critical checks with current-data findings. The findings are saved in `audit.dq_results`; the exit is the intended quality-gate behavior, not a load crash.
