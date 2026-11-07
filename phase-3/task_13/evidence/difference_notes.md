# Task 13 comparison and difference notes

## Grain and join order

The comparison table contains 198 rows: 11 departments by 18 months (Apr 2025–Sep 2026). Payroll, attendance, and headcount were aggregated separately to department-month before joining. Approved leave was assigned to the SCD department using `employee_key`, split across covered months by the share of calendar working days, and then aggregated to the same grain. This avoids multiplying fact rows in a many-to-many join.

## PQ-13 reference comparison

`comparison_table.csv` contains one row per department-month, actuals, reference values, differences for all 13 shared measures, plus approved leave days and leave days per head. All 2,574 reference checks (198 rows × 13 measures) match within the displayed source precision. Differences are calculated as actual minus reference. Reference task counts, story points, and task-completion measures are not in the four-source scope of this task; leave also has no reference field.

The initial comparison had differences tied to the exact planted records listed in the DQ known-issues file. Task 13 excludes these flagged rows from its aggregate view and preserves the source facts unchanged:

| DQ issue | Excluded record IDs | Reason |
|---|---|---|
| DQ-02 duplicate payroll | PI-X0001, PI-X0002 | Duplicate employee-month payroll rows. |
| DQ-03 orphan payroll | PI-X0003, PI-X0004 | Employee IDs do not exist in `dim_employee`. |
| DQ-01 attendance after exit | FA-X0001, FA-X0002, FA-X0003, FA-X0004 | Attendance recorded after the employee left. |

After these documented exclusions, employer cost, gross pay, paid employee counts, cost per head, overtime share, attendance, and late-arrival totals reconcile to the PQ-13 reference. No source rows were deleted or rewritten.

## Leave allocation note

Only Approved leave is included. One approved request (LR-002286) has an end date before its start date. Its recorded two leave days are assigned to the start month and flagged on the dashboard for source review. The other reversed-date request (LR-000025) is Rejected and is excluded by the approved-status rule. Leave measures are additions to the department view and cannot be checked against this reference because it has no leave columns.

## Interpretation

The three-panel chart compares employer cost, overtime cost, and attrition for each department-month; co-movement shows association only. Staffing shortages, seasonal demand, department and role mix, tenure, leave, management changes, and exit reasons are possible confounders. The chart alone cannot establish that overtime causes attrition.
