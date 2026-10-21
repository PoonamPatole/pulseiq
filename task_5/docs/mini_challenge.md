# Phase 1 mini-challenge: M29 headcount growth

## Definition

**Name:** Headcount growth (month over month)  
**ID:** M29  
**Business definition:** Percentage change in period-end headcount from the previous month.  
**Formula:** `(current month headcount - previous month headcount) / previous month headcount * 100`  
**Grain:** Company-month or department-month.  
**Source:** Governed M01 company or department headcount metric views.  
**Privacy:** Suppress groups below five.

The view is `metrics.m29_headcount_growth_mom`. It is listed in `metrics.metric_catalog` and displayed as a KPI on the Workforce page. The first month has no prior month, so it is not assigned a percentage.

## Calculator check

At company level, August 2026 headcount is 427 and September 2026 headcount is 441:

`(441 - 427) / 427 * 100 = 3.278689...%`

Rounded to two decimals, M29 is **+3.28%** for September 2026. Re-run the metric builder and verify with:

```sql
SELECT month_start_date, headcount, previous_headcount, metric_value
FROM metrics.m29_headcount_growth_mom
WHERE scope = 'Company'
  AND month_start_date = DATE '2026-09-01';
```

The selected-department version uses the same formula over that department's privacy-filtered M01 values.
