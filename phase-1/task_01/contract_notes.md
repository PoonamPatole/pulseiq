# PulseIQ contract notes

Source: `data/03_Data/csv/data_contracts.csv`. “Nullable: no” means the value is required; “yes” means blank is permitted subject to any rule shown.

## `fact_anomaly` — AI anomaly results

| Column | Type | Nullable? | Contract promise / allowed values |
|---|---|---:|---|
| `result_id` | string | No | Unique; format `AN-nnnn`. |
| `source_dataset` | string | No | `attendance_monthly_features` or `payroll_monthly_features`. |
| `record_id` | string | No | Must exist in the named source dataset. |
| `employee_id` | string | No | Must exist in `dim_employee`. |
| `period` | date | No | Month-end or month-start date. |
| `anomaly_score` | decimal(4,3) | No | Between 0 and 1. Higher means more unusual. |
| `flagged` | char(1) | No | `Y` or `N`. |
| `reason_code` | string | No | Must be one of the published codes. |
| `reason_text` | string | No | Plain-English explanation. |
| `money_at_risk` | decimal(14,2) | Yes | Blank for attendance rows; estimated money exposure for payroll rows. |
| `model_version` | string | No | Semantic-version text. |
| `scored_at` | timestamp | No | UTC timestamp. |

## `fact_forecast` — AI forecasts

| Column | Type | Nullable? | Contract promise / allowed values |
|---|---|---:|---|
| `forecast_id` | string | No | Unique; format `FC-nnnn`. |
| `metric` | string | No | `headcount_end` or `attrition_rate_monthly_pct`. |
| `department_id` | string | No | Department ID or `ALL`. |
| `forecast_month` | date | No | First day of the month. |
| `forecast_value` | decimal | No | Must be greater than or equal to 0. |
| `lower_80` | decimal | No | Must be less than or equal to `forecast_value`. |
| `upper_80` | decimal | No | Must be greater than or equal to `forecast_value`. |
| `method` | string | No | Forecast method text. |
| `trained_through` | string | No | Format `YYYY-MM`; last actual month used. |

## `fact_task` — Task board

| Column | Type | Nullable? | Contract promise / allowed values |
|---|---|---:|---|
| `task_id` | string | No | Unique; format `TASK-nnnnn`. |
| `team_id` | string | No | Must exist in `dim_team`. |
| `sprint_id` | string | No | Must exist in `dim_sprint`. |
| `assignee_employee_id` | string | No | Must exist in `dim_employee`. |
| `task_type` | string | No | `Feature`, `Bug`, `Chore`, or `Spike`. |
| `priority` | string | No | `P1`, `P2`, `P3`, or `P4`. |
| `story_points` | int | No | One of `1`, `2`, `3`, `5`, `8`, `13`. |
| `created_date` | date | No | Must be on or before `started_date`. |
| `started_date` | date | Yes | Blank only when status is `To Do`. |
| `due_date` | date | No | Must be the sprint end date. |
| `completed_date` | date | Yes | Required when status is `Done`; when present, must be on or after `started_date`. |
| `status` | string | No | `Done`, `In Progress`, `Blocked`, `To Do`, or `Cancelled`. |
| `reopened_count` | int | No | Must be greater than or equal to 0. |

## Scope notes

- The `data_contracts.csv` supplied with the project defines these three feeds and `fact_attrition_risk`.
- For the eight other fact feeds, the starter provides no allowed-value/business-rule contracts. The pipeline validates every column's type and nullability against `data_dictionary.csv`, marks these rows `DICTIONARY_SCHEMA_VALIDATED`, and does not invent allowed-value lists.
- The source `fact_task` table also contains `cycle_time_days`, `is_overdue_at_cutoff`, and `completed_on_time`; the supplied detailed contract does not define them. Their type and nullability are checked from the data dictionary, but no additional allowed-value/business rules are available.
- Unexpected columns produce a warning and are retained so no source data disappears; the warning requires an analyst to review and update the contract before downstream use.
- Numeric-looking identifiers declared as text by the dictionary are converted to text in `clean` only; `raw` remains unchanged.
- “Unique” and reference-existence promises require checking the row against other rows or tables, not just checking its data type.
- The task contract says `due_date` must equal the sprint end date. Confirm the sprint end date from `dim_sprint` when implementing that cross-table check.
