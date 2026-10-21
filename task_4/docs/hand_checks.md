# Five metric hand checks

Run `python .\task_4\create_metric_views.py` first. These examples compare simple source components with the reusable view result. Numbers below use the current Task 2 warehouse; values based on facts with unresolved Task 3 failures are provisional.

| Metric | Selected group | Source arithmetic | View value | Check |
|---|---|---:|---:|---|
| M01 Headcount | D01, September 2026 | `headcount_end = 167` | 167 | Match |
| M04 Monthly attrition | D01, September 2026 | `2 exits / 160 starting headcount × 100` | 1.25% | Match |
| M07 Gross pay | D01, September 2026 | `SUM(gross_pay) = 20,720,901.38` across 169 employees | 20,720,901.38 INR | Match |
| M16 Revenue | Account 4001, April 2025 | `-SUM(signed_amount_debit_positive) = 41,824,400` across 23 lines | 41,824,400 INR | Match |
| M22 Task completion | Team T01, sprint SP-01 | `50 done / 55 non-cancelled = 0.909091` | 0.909091 (90.91%) | Match |

## Attrition denominator decision

For the M04 example, start headcount is 160 and end headcount is 167. The chosen start-headcount denominator gives 1.25%. Ending headcount gives `2 / 167 × 100 = 1.20%`; average headcount gives `2 / ((160 + 167) / 2) × 100 = 1.22%`. M04 follows the official dictionary formula. Rolling M05 uses its separately specified 12-month average-end-headcount formula.

## Re-run by hand

```sql
SELECT * FROM metrics.m01_headcount
WHERE month_start_date = DATE '2026-09-01' AND department_id = 'D01';

SELECT SUM(exits) AS exits, SUM(headcount_start) AS starting_headcount,
       100.0 * SUM(exits) / NULLIF(SUM(headcount_start), 0) AS calculated_pct
FROM warehouse.fact_headcount_monthly
WHERE month_start_date = DATE '2026-09-01' AND department_id = 'D01';

SELECT * FROM metrics.m07_gross_pay
WHERE month_end_date = DATE '2026-09-30' AND department_id = 'D01';

SELECT * FROM metrics.m16_revenue
WHERE month_start_date = DATE '2025-04-01' AND account_code = 4001;

SELECT * FROM metrics.m22_task_completion_rate
WHERE team_id = 'T01' AND sprint_id = 'SP-01';
```
