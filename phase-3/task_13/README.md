# Task 13 — Cross-department impact view

Build the four-source department-month view and PQ-13 comparison, then launch the dashboard from the project root:

```powershell
.\.venv\Scripts\python.exe .\phase-3\task_13\build_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\phase-3\task_13\app.py
```

Payroll, attendance, and headcount are aggregated to department and month before joining. Approved leave is joined to `dim_employee` with `employee_key` so the department version for the request is respected. Multi-month leave is allocated by the share of working days in each month; its total stays equal to the recorded request days. One approved request has an end date before its start date; its recorded two days are retained in the start month and flagged for source review.

The Task 13 aggregate excludes only the eight record IDs documented in DQ-01, DQ-02, and DQ-03 (four after-exit attendance rows, two duplicate payroll rows, and two orphan payroll rows). The source facts remain unchanged. The PQ-13 comparison covers 13 measures shared with these four sources; task-board fields in the broader reference file are outside this task.

Payroll cost, gross pay, overtime cost and hours are summed. Attendance is the weighted M13 rate: `(present_days + 0.5 × half_days_unpaid) / scheduled_days`. Attrition is `exits / headcount_start × 100`. Cost per head is employer cost divided by distinct employees paid; overtime share is overtime pay divided by employer cost; leave days per head uses month-end headcount.

The PQ-13 reference file also contains task-board measures. This task reconciles the fields shared with its four source facts; reference task counts and completion measures are not part of this view. Leave measures have no reference columns.
