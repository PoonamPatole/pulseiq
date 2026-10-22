# PulseIQ Phase 1 Report

**Name:** Poonam Satish Patole  
**Track:** Data Analysts  
**Phase:** Phase 1  
**Prepared:** 23 October 2026  
**GitHub repository:** [PoonamPatole/pulseiq](https://github.com/PoonamPatole/pulseiq)  
**Git tag:** `phase-1`

## Task status and evidence

| Task | Status | Evidence |
|---|---|---|
| 1. ETL and data contracts | Complete locally; detailed rules apply to four feeds, and the dictionary supplies type/null checks for all remaining fact columns. | [Current ETL results](task_1/evidence/current_run.md); [contract notes](task_1/contract_notes.md) |
| 2. Star-schema warehouse | Complete locally; all 12 fact row counts reconcile and 261 relationship exceptions are documented. | [Star schema and audit notes](task_2/docs/star_schema.md); [reconciliation results](task_2/evidence/reconciliation.md) |
| 3. Data-quality gatekeeper | Complete locally; all 14 checks run, each test detects an injected defect, and 11 of 11 planted issue categories were detected. | [DQ issue comparison](task_3/docs/missed_issues.md); run `python .\task_3\dq_gatekeeper.py --self-test` |
| 4. Governed metric layer | Complete locally; 28 supplied metrics, M29, catalog, privacy thresholds, and five hand checks are documented. | [Hand checks](task_4/docs/hand_checks.md); [metric decisions](task_4/docs/metric_decisions.md) |
| 5. Workforce dashboard | Complete locally; app test passes and screenshots show the KPI cards, M29, trend, department/location charts, and full work-mode chart. | [App validation](task_5/evidence/app_validation.md); screenshots in `task_5/evidence/`; [CEO questions](task_5/pages/02_CEO_Questions.py) |

## Proof it works

1. All 29 CSV files match their `raw` DuckDB row counts.
2. Task 1 rerun verification compared raw, clean, summary, and quarantine contents across two consecutive runs: all 54 materialized tables were stable. The audit run log and DQ result timestamps intentionally change on each run.
3. All 12 warehouse facts reconcile to Task 1 passed counts. Task 1 quarantines 20 bad `fact_task` rows with a written reason; the other fact tables have no quarantined rows.
4. The 14-check gatekeeper detects all 11 planted issue categories. The supplied data currently produces five Critical DQ checks with findings, so the ETL command intentionally exits with code 1 after saving its audit results. This is a data-quality gate failure, not a load crash.
5. The Streamlit app test reports zero exceptions, four KPI cards, four charts, one department selector, and one date-range control. September 2026 headcount is 441 and M29 month-over-month growth is +3.28%. Dashboard screenshots are included in `task_5/evidence/` and in this report.
6. M28 forecast error is `NULL` with `NO_ACTUALS_YET` because actual values for forecast months are not supplied.

## What I learned

DuckDB stores a whole analytics database in one local file and can load CSV data directly.  
A star schema keeps measurable events in fact tables and descriptive context in dimensions.  
An employee surrogate key preserves which department was valid when a historical event happened.  
Data contracts and quality checks make failures visible instead of silently hiding them.  
Metric views give dashboards one reusable definition for each business number.

## Problems and solutions

1. The starter contract sheet defines detailed rules for only four feeds. I applied the provided data dictionary's type and nullability to every fact column, and did not invent allowed-value rules for the remaining feeds.
2. CSV type inference initially treated numeric-looking text identifiers as numbers. The pipeline converts those values only in `clean`; the raw source remains unchanged.
3. The quality gate finds existing payroll, key, history, and minimum-group-size issues. They are recorded in `audit.dq_results` and quarantines rather than removed silently.
4. The dataset has 261 explainable relationship exceptions: employee history date gaps, forecast dates beyond the supplied calendar, and two payroll rows with employee key `-1`.
5. The saved dashboard screenshots show the KPI row, trend, filters, and workforce breakdown charts.

## Plan for Phase 2

Resolve or formally accept the Critical data-quality findings with documented owners. Then extend the dashboard to attendance, attrition, teams, and payroll cost, using the existing governed metric views and preserving small-group privacy thresholds.

