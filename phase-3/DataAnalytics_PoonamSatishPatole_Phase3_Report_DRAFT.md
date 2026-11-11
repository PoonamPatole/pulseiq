# PulseIQ Analytics — Phase 3 Report

**Name:** Poonam Satish Patole  
**Track:** Data Analysts  
**Phase:** Phase 3  
**Prepared:** 5 November 2026  
**GitHub repository:** [PoonamPatole/pulseiq](https://github.com/PoonamPatole/pulseiq)  
**Git tag:** Phase-3

## Task status and evidence

| Task | Status | Evidence |
|---|---|---|
| 11. P&L and expense analytics | Complete locally; monthly revenue, net profit, and operating margin tie to governed M16–M18 views. | [findings and tie-out](task_11/evidence/findings.md) |
| 12. Invoices, receivables, and cash flow | Complete locally; receivables ageing, payment timing, cash movement, and bucket check are built. | [Task 12 README](task_12/README.md), [bucket check](task_12/evidence/bucket_total_check.csv) |
| 13. Cross-department impact | Complete locally; 13 shared measures reconcile to PQ-13 after documented exclusions. | [comparison and difference notes](task_13/evidence/difference_notes.md) |
| 14. AI signals and forecasts | Complete locally; anomaly exposure and forecast intervals are presented with uncertainty and data limits. | [forecast and anomaly notes](task_14/evidence/forecast_notes.md) |
| 15. Executive company-health scorecard | Complete locally; eight governed KPIs include targets only where supplied. | [KPI selection](task_15/evidence/kpi_selection.md) |

## Proof it works

The Task 11–15 metric builders were run from the project virtual environment on 5 November 2026. All five completed with exit code 0 and created their metric views in `pulseiq.duckdb`.

- **Task 11:** Ledger counts in the workbook and warehouse match: 6,784 ledger rows and 501 expense rows. Across 18 months (April 2025–September 2026), revenue, net profit, and operating margin tie to governed metrics M16–M18 to the cent, except for floating-point precision in margins. April 2026 revenue rose 11.4% from March while expenses rose 20.7%; net profit fell from INR 15.48m to INR 11.45m.
- **Task 12:** Receivable balances are split into mutually exclusive ageing bands of 0–30, 31–60, 61–90, and over 90 days. The open-balance bucket check is included as evidence. Cash in uses invoice payment dates; cash out uses paid expense bills including GST.
- **Task 13:** The comparison covers 11 departments, 18 months, and 13 shared measures: 2,574 checks in total, all matching PQ-13 within displayed precision after the documented exclusions. Source facts remain unchanged. Task-board measures and leave are outside the reference comparison.
- **Task 14:** The source has 405 flagged anomaly rows. Payroll anomaly estimates total INR 31,421,239.07 across 184 quantified records; this is potential exposure for human review, not confirmed loss. There are 12 company-level forecasts for October 2026–March 2027. Actuals end in September 2026, so forecast error and MAPE are not yet available.
- **Task 15:** The scorecard presents headcount, revenue, net profit, operating margin, attrition, attendance, overtime share, and task completion. Targets are taken only from the supplied target table. Four KPIs have no numeric target and are labelled accordingly.

The task evidence includes tie-out and comparison CSVs, screenshots, and written calculation notes. This report confirms successful metric-view builds; it does not claim a separate Streamlit app test run for Tasks 11–15.

## What I learned

Financial measures need a clear source and grain: vendor bills are not the same as all ledger expenses, and invoice cash dates differ from accrual dates. Department-level comparisons are safer when each fact is aggregated to the same grain before joining. Model flags and forecasts communicate signals with uncertainty; they do not establish confirmed loss or explain causes. Executive targets should come from an agreed source rather than inferred thresholds.

## Problems and how I handled them

The workbook headline values are dataset counts rather than a monthly P&L answer key, so Task 11 ties to governed metrics instead. Task 13 excludes four after-exit attendance rows, two duplicate payroll rows, and two orphan payroll rows from its comparison aggregate, with record IDs documented; it does not delete or rewrite source facts. One approved leave request has a reversed date range and is assigned to its start month for review. Task 14 has no actuals for the forecast horizon, and blank attendance anomaly money estimates are not treated as zero. Task 15 leaves four KPIs without targets unscored.

## Plan for the next phase

Review the documented payroll and source-data exceptions with the responsible owners, refresh forecast comparisons when actual periods arrive, and confirm any KPI targets with business stakeholders. Package the dashboards and release evidence for the final submission, then record the approved release tag and repository reference.
