# Data quality checks: plain-English meaning and response

The catalog contains 14 checks. Critical checks stop downstream use because they can change financial totals, duplicate records, break joins, violate history, make the pipeline stale, or leave privacy settings unsafe. Warning checks are still logged and owned, but do not stop the load.

| ID | What could go wrong | Severity / action |
|---|---|---|
| DQ-C01 | Payroll employer cost differs from salary-related ledger expense for a month. | Critical: stop and reconcile payroll posting to ledger accounts 5001–5005. |
| DQ-C02 | Debits and credits do not balance within a journal entry. | Critical: stop and reject or repair the entry. |
| DQ-C03 | An employee has more than one payroll row for the same run. | Critical: stop; duplicate pay rows can overstate payroll. |
| DQ-C04 | A payroll employee ID has no matching employee dimension record. | Critical: stop; downstream employee attribution is unreliable. |
| DQ-C05 | Attendance occurs after the employee’s recorded exit month. | Warning: ask HR to confirm the exit date or attendance row. |
| DQ-C06 | Attendance has unpaid absence days that are not reflected in payroll LOP days within the 0.5-day tolerance. | Warning: review the attendance-to-payroll mapping. |
| DQ-C07 | An invoice has payments above its total or a negative balance. | Warning: review the invoice and payment data. |
| DQ-C08 | An expense total differs from pre-GST amount plus GST by more than INR 0.01. | Warning: correct the expense entry. |
| DQ-C09 | A task completes before it starts, or a `Done` task has no completion date. | Warning: ask Engineering Ops to correct task dates/status. |
| DQ-C10 | A leave request ends before it starts. | Warning: correct the leave dates. |
| DQ-C11 | Attrition predictions are more than seven days behind their batch, or anomaly scores are over 24 hours older than the latest successful load. | Warning: ask the AI team to refresh the feed. |
| DQ-C12 | Two SCD Type 2 employee versions overlap in validity dates. | Critical: stop; a fact date could map to two employee versions. |
| DQ-C13 | There is no successful ETL run in the last 24 hours. | Critical: stop and check the scheduler/source. |
| DQ-C14 | An employee-sensitive metric lacks a valid positive minimum group size. | Critical: do not publish until the privacy threshold is configured. |

DQ-C14 checks the threshold configuration. A manager-facing aggregate must also apply that threshold in its query, for example:

```sql
GROUP BY department_id, period_end_date
HAVING COUNT(DISTINCT employee_id) >= minimum_group_size
```

The supplied metric dictionary uses values such as `5` and `5 tasks`; the check extracts the numeric threshold. Blank thresholds are permitted for metrics that do not expose employee-level groups, but employee-sensitive metrics M01–M15, M19, M22–M27 must have a positive threshold.
