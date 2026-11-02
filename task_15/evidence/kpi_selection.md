# Task 15 KPI selection

| KPI | Governed metric | Why a founder needs it |
|---|---|---|
| Company headcount | M01 | Shows the size of the workforce available to deliver the plan. |
| Revenue | M16 | Shows the scale of sales activity in the selected month. |
| Net profit | M17 | Shows what remains after the costs included in the governed P&L. |
| Operating margin | M18 | Shows how much of revenue remains as operating profit. |
| Monthly attrition | M04 | Signals whether the company is retaining its workforce. |
| Attendance rate | M13 | Indicates whether scheduled staff capacity is present. |
| Overtime share | M11 | Helps reveal workload pressure and additional payroll exposure. |
| Task completion | M22 | Gives a view of delivery progress against planned work. |

## If only five KPIs fit

Keep revenue, net profit, operating margin, attrition and attendance. Together they cover commercial scale, profitability, efficiency and workforce stability. Remove headcount because it is a capacity context measure, overtime share because it is a workload-cost detail that can be reviewed on the department page, and task completion because it is an execution measure best reviewed on the delivery page.

## Target coverage

The supplied `warehouse.kpi_targets` contains targets for attrition, attendance, overtime share and task completion. It does not supply numeric targets for headcount, revenue, net profit or operating margin. Those four show `NO TARGET`; no threshold is inferred.
