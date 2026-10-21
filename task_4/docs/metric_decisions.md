# Metric-layer decisions

## Naming and catalog

Each view is named `metrics.mNN_<short_name>` using the ID in `raw.metric_dictionary`. `metrics.metric_catalog` keeps the official definition, source, grain, owner, unit, caveat, and effective minimum group size.

## Attrition denominator

M04 follows the dictionary formula: monthly exits divided by the month's starting headcount. The September 2026 D01 example has 2 exits and starting headcount 160, so the displayed rate is 2 / 160 × 100 = 1.25%. Using ending headcount (167) would give 1.20%; using the average of start and end (163.5) would give 1.22%. M05 and M06 are separate rolling 12-month measures and use average month-end headcount as stated in their dictionary formulas.

## Privacy and grain

Views never return employee names or employee IDs. Pay and payroll measures are grouped by department and month, even where the dictionary describes an employee-month source grain. This keeps individual salary out of manager-facing results. Each view filters groups using its effective minimum group size.

Three metric dictionary rows have no numeric minimum: M19, M24, M26. The metric catalog uses explicit working thresholds: 5 employees for M19, 5 completed tasks for M24, and 10 scored records for M26. M22, M23, and M25 parse the dictionary's text thresholds such as `5 tasks`. The source dictionary stays unchanged; its missing values remain visible in `dictionary_minimum_group_size`.

## Other calculation choices

- M16 uses credit-normalized revenue as negative debit-positive ledger amount for accounts 4001–4004.
- M17 includes all 4xxx and 5xxx accounts, including 4900 interest income, as the dictionary caveat says.
- M19 uses ledger accounts 5001–5005 for payroll cost and 4001–4004 for revenue.
- M20 is a point-in-time DSO as of 30 September 2026. Invoice balances are only supplied as a cutoff snapshot, so the view does not claim to reconstruct historical monthly balances.
- M21 uses the workbook cutoff date (30 September 2026) for overdue balances.
- M25 excludes negative cycle times, which the metric dictionary identifies as data errors.
- M28 returns a NULL metric and `NO_ACTUALS_YET` until actual headcount arrives for a forecast month.

## Gate status

These views define formulas; they do not clean or repair their source facts. Task 3 currently reports critical data-quality failures, so payroll and other affected-source metrics must be considered provisional until those failures are resolved.
