# Task 2 reconciliation evidence

Built from `audit.warehouse_reconciliation` after rebuilding the warehouse on 2026-10-19.

| Fact | Task 1 rows passed / retained | Warehouse rows | Count matches? | Task 1 validation scope |
|---|---:|---:|---|---|
| `fact_anomaly` | 405 | 405 | Yes | Detailed contract + dictionary schema |
| `fact_attendance_monthly` | 7,343 | 7,343 | Yes | Dictionary type/nullability |
| `fact_attrition_risk` | 430 | 430 | Yes | Detailed contract + dictionary schema |
| `fact_expense` | 501 | 501 | Yes | Dictionary type/nullability |
| `fact_forecast` | 72 | 72 | Yes | Detailed contract + dictionary schema |
| `fact_headcount_monthly` | 891 | 891 | Yes | Dictionary type/nullability |
| `fact_invoice` | 743 | 743 | Yes | Dictionary type/nullability |
| `fact_invoice_payment` | 709 | 709 | Yes | Dictionary type/nullability |
| `fact_leave` | 3,441 | 3,441 | Yes | Dictionary type/nullability |
| `fact_ledger` | 6,784 | 6,784 | Yes | Dictionary type/nullability |
| `fact_payroll` | 7,344 | 7,344 | Yes | Dictionary type/nullability |
| `fact_task` | 28,848 | 28,848 | Yes | Detailed contract + dictionary schema; 20 rows quarantined in Task 1 |

**Result:** 12 of 12 warehouse fact row counts reconcile. For eight facts, the starter supplies no allowed-value/business-rule rules; Task 1 still checks their columns against the dictionary's types and nullability.

## Orphan relationship audit

The build records 261 relationship exceptions in `audit.orphan_rows` and does not drop the fact rows: 202 task assignee SCD date gaps, 21 anomaly employee SCD date gaps, 36 forecast dates beyond the supplied calendar, and 2 payroll rows using employee key `-1`. The rationale is documented in `docs/star_schema.md`.
