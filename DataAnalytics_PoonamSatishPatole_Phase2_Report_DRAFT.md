# PulseIQ Analytics — Phase 2 Report

**Name:** Poonam Satish Patole  
**Track:** Data Analysts  
**Phase:** Phase 2  
**GitHub repository:** [PoonamPatole/pulseiq](https://github.com/PoonamPatole/pulseiq)  
**Git tag:** Phase-2

## Task status and evidence

| Task | Status | Evidence |
|---|---|---|
| 6. Attendance and leave | Complete locally; attendance, overtime, late arrivals, and approved leave are shown with scope caveats. | [attendance observations](task_6/evidence/insights.md) |
| 7. Attrition analytics | Complete locally; actual exits and grouped risk estimates are separate, with groups under five suppressed. | [three recorded findings](task_7/evidence/findings.md) |
| 8. Team productivity | Complete locally; delivery measures are shown, and two team velocity checks match by hand. | [two-team manual verification](task_8/evidence/verification.md) |
| 9. Payroll cost and reconciliation | Complete locally; figures are provisional pending Finance review of five monthly differences and duplicate/orphan records. | [five-month reconciliation](task_9/evidence/exclusions.md) |
| 10. Budget and KPI targets | Complete locally; budget variance and target status are shown, with three hand checks matching. | [three manual variance checks](task_10/evidence/verification.md) |

## Proof it works

The five Streamlit dashboards and their evidence were produced in the local project. The documented checks give these results:

- **Task 6:** with all departments selected, the lowest observed monthly attendance rates were May 2026 at **92.64%**, January 2026 at **93.11%**, and June 2026 at **93.16%**. Overtime and holiday context are recorded alongside the rates; these observations do not establish the cause of an attendance change.
- **Task 7:** a query matching the dashboard’s monthly department aggregation returned the three largest exit rows: Engineering, Mar 2025, **5 exits / 3.40%**; Operations & IT, Mar 2024, **4 / 13.79%**; and Engineering, Apr 2025, **3 / 2.10%**. Predicted risk is shown separately and grouped to protect small groups.
- **Task 8:** direct checks of `warehouse.fact_task` for sprint SP-01 matched dashboard velocity for both teams: Analytics & BI had **22 completed tasks and 79 points**; Data Platform had **29 completed tasks and 72 points**.
- **Task 9:** treat payroll figures as **provisional pending Finance review**. The Task 3 payroll-to-ledger comparison (DQ-C01) returns **five mismatched months**. June 2026 is **−INR 18,450** (payroll minus ledger); the other four differences are recorded for investigation. Duplicate employee/run rows and unmatched employee IDs also remain unresolved. The answer key is company-level and does not prove department allocations. No payroll rows were excluded.
- **Task 10:** three April 2025 hand calculations match dashboard actual-minus-budget variances: Engineering **−INR 1,911,891.25 (−8.19%)**, Product & Design **−INR 461,307.33 (−8.73%)**, and Data & AI **−INR 100,184.00 (−1.32%)**. Negative values indicate underspend.

These are local data checks and manual reconciliations documented with the task evidence. No automated Streamlit app test report is recorded for Tasks 6–10, so the evidence here does not claim one.

## What I learned

Attendance and leave measures can have different grains, so the leave chart needs a company-wide caveat.  
Actual exits and modelled attrition risk answer different questions and should stay separate.  
Team velocity is easier to interpret when checked against completed task rows and sprint context.  
Payroll and budget comparisons need clear sign conventions, traceable sources, and visible uncertainty.

## Problems and how I handled them

The monthly attendance feed does not support reliable long-weekend labels, so I use calendar holidays as context and avoid claiming a cause. The attrition risk data includes small groups, so the dashboard suppresses groups below five and shows no individual risk scores. Payroll has duplicate employee/run groups, orphan employee IDs, and five payroll-to-ledger mismatches; I preserved the source rows and documented the five differences rather than guessing which entries to remove. The supplied reconciliation key is company-level, so it cannot validate department allocations. For KPI targets, I documented the variance direction and checked three rows by hand to make underspend and overspend clear.

## Plan for the next phase

Prepare the final submission by making the dashboards available through a shareable deployment, checking access from another device, and completing the release materials and demo. Keep the current payroll exceptions visible until Finance confirms corrections, then update the evidence and quality findings with the approved resolution. Apply the `phase-2` Git tag after the report and phase files are committed, and record the final release reference in the submission.
