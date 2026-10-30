# PulseIQ Analytics

## Phase 1

PulseIQ is a five-task data analytics project that loads source CSVs into DuckDB, validates data quality, builds a star-schema warehouse, creates governed metric views, and presents workforce metrics in a Streamlit dashboard.

- **GitHub:** [PoonamPatole/pulseiq](https://github.com/PoonamPatole/pulseiq)
- **Phase 1 tag:** `phase-1`
- **Database:** `pulseiq.duckdb` (created locally; it is excluded from Git)

## Project flow

```text
Source CSVs → Task 1 load and validation → Task 3 quality gate
            → Task 2 warehouse → Task 4 governed metrics
            → Task 5 Streamlit dashboard
```

Task 1 also invokes the Task 3 gatekeeper after loading. The warehouse and dashboard use the loaded data and governed views; results affected by unresolved quality findings should be treated as provisional.

## Requirements and setup

Use Python 3.10 or newer on Windows. From the project root in PowerShell, create the virtual environment and install the project dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\data\05_Starter\requirements.txt
```

If `.venv` already exists, skip the first command. All commands below use its Python executable, so activation is not required.

## Build and run the project

Run these from the project root, in order:

```powershell
.\.venv\Scripts\python.exe .\task_1\etl.py
.\.venv\Scripts\python.exe .\task_1\check_row_counts.py
.\.venv\Scripts\python.exe .\task_2\build_warehouse.py
.\.venv\Scripts\python.exe .\task_4\create_metric_views.py
.\.venv\Scripts\python.exe .\task_5\build_workforce_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\task_5\app.py
```

Run the ETL before the row-count check because the check reads tables from the local DuckDB database. The Task 1 ETL currently finds five Critical data-quality checks and may exit with code 1 after it has written the load and audit results. This is the gate's expected response for the supplied data. Review `audit.dq_results`; when running the training dashboard, continue with Tasks 2–5 while treating affected metrics as provisional.

Streamlit opens the **Workforce and headcount** dashboard in a browser. Use its sidebar to filter the department and month range. The **CEO Questions** page explains the five questions the dashboard addresses.

## The five tasks

### Task 1 — Raw loading and contract validation

Loads the CSV feeds into the DuckDB `raw` schema, applies supplied contracts and dictionary type/nullability checks, and writes clean, quarantine, summary, and load-log tables. Detailed business rules are supplied for four feeds; unsupported rules are not invented for the others.

- Main code: [`task_1/etl.py`](task_1/etl.py)
- Count check: [`task_1/check_row_counts.py`](task_1/check_row_counts.py)
- Rerun verification: [`task_1/verify_rerun.py`](task_1/verify_rerun.py)
- Results: [`task_1/evidence/current_run.md`](task_1/evidence/current_run.md)

### Task 2 — Star-schema warehouse

Builds warehouse dimensions and facts with keys, then records row-count reconciliation and relationship exceptions in the `audit` schema.

- Main code: [`task_2/build_warehouse.py`](task_2/build_warehouse.py)
- Schema and join guide: [`task_2/docs/star_schema.md`](task_2/docs/star_schema.md)
- Reconciliation: [`task_2/evidence/reconciliation.md`](task_2/evidence/reconciliation.md)

### Task 3 — Data-quality gatekeeper

Runs 14 quality checks and records results in `audit.dq_results`. Critical findings fail the gate after the results have been saved; warnings are recorded without stopping the load. The scratch-only self-test injects sample defects to check that the rules detect them.

```powershell
.\.venv\Scripts\python.exe .\task_3\dq_gatekeeper.py --self-test
```

- Main code: [`task_3/dq_gatekeeper.py`](task_3/dq_gatekeeper.py)
- Check explanations: [`task_3/docs/check_explanations.md`](task_3/docs/check_explanations.md)
- Current data includes Critical findings; check the latest `audit.dq_results` before treating downstream metrics as production-ready.

### Task 4 — Governed metric layer

Creates views for the 28 supplied metrics plus M29 in the DuckDB `metrics` schema. The views document formulas, grain, caveats, and minimum group thresholds; small groups are suppressed.

- Main code: [`task_4/create_metric_views.py`](task_4/create_metric_views.py)
- Calculation decisions: [`task_4/docs/metric_decisions.md`](task_4/docs/metric_decisions.md)
- Hand checks: [`task_4/docs/hand_checks.md`](task_4/docs/hand_checks.md)
- M28 forecast error remains `NULL` with `NO_ACTUALS_YET` where no actual headcount is available for the forecast month.

### Task 5 — Workforce and headcount dashboard

Creates dashboard-safe aggregate views and serves a Streamlit app. The Workforce page has period-end headcount, period change, average headcount, M29 month-over-month growth, a trend chart, and department, city-tier, and work-mode comparisons. It reads `metrics.*` views and suppresses groups below the configured threshold. The second page lists the CEO questions and metric/privacy notes.

- Dashboard: [`task_5/app.py`](task_5/app.py)
- Dashboard metric setup: [`task_5/build_workforce_metrics.py`](task_5/build_workforce_metrics.py)
- CEO questions: [`task_5/pages/02_CEO_Questions.py`](task_5/pages/02_CEO_Questions.py)
- Validation and screenshots: [`task_5/evidence/`](task_5/evidence/)
- M29 definition and hand calculation: [`task_5/docs/mini_challenge.md`](task_5/docs/mini_challenge.md)

## Data and outputs

- Source workbook and CSV files are under [`data/03_Data/`](data/03_Data/).
- Starter dependencies and loader are under [`data/05_Starter/`](data/05_Starter/).
- The DuckDB database is created at the project root as `pulseiq.duckdb`; it is ignored by Git and can be rebuilt by running the pipeline.
- Task-specific notes, diagrams, and evidence are kept in each `task_1` through `task_5` folder.

The supplied training data has unresolved Critical quality findings, including payroll-related issues. The quality gate preserves and reports these findings rather than silently dropping the affected source rows. Treat metrics from affected sources as provisional until the findings are resolved or formally accepted.

## Phase 2

Phase 2 extends the analytics work with five Streamlit dashboards for attendance and leave, attrition, team productivity, payroll reconciliation, and budget and KPI targets. Tasks 6-10 reuse the warehouse and add their own metric preparation, analysis, validation, and evidence.

- **Phase 2 report:** [PDF](DataAnalytics_PoonamSatishPatole_Phase2_Report_DRAFT.pdf) | [Markdown](DataAnalytics_PoonamSatishPatole_Phase2_Report_DRAFT.md)
- **Git tag:** `Phase-2`
- **Task dashboards:** Tasks 6-9 read from the project DuckDB warehouse; Task 10 first builds its budget and target metric views.

## Requirements and setup

Use the Python environment and dependencies described in Phase 1. From the project root, run the Phase 1 data pipeline first so the DuckDB database and warehouse tables are available. Task 10 also requires its own metric build step before its dashboard is launched.

## Build and run the Phase 2 dashboards

Run these from the project root in PowerShell, in order:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\task_6\app.py
.\.venv\Scripts\python.exe -m streamlit run .\task_7\app.py
.\.venv\Scripts\python.exe -m streamlit run .\task_8\app.py
.\.venv\Scripts\python.exe -m streamlit run .\task_9\app.py
.\.venv\Scripts\python.exe .\task_10\build_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\task_10\app.py
```

Each Streamlit command starts one dashboard. Run the Task 10 builder after the Phase 1 warehouse is ready and before launching the Task 10 app.

## The five Phase 2 tasks

### Task 6 - Attendance and leave

Shows attendance rate, late arrivals, overtime, approved leave, and holiday context. Attendance follows the M13 calculation, including half-day adjustments. Leave is shown company-wide because the leave fact has no department key; holidays provide context but do not establish a cause for attendance changes.

- Dashboard: [`task_6/app.py`](task_6/app.py)
- Findings: [`task_6/evidence/insights.md`](task_6/evidence/insights.md)
- Dashboard notes: [`task_6/README.md`](task_6/README.md)

### Task 7 - Attrition analytics

Separates actual exits and voluntary exits from grouped predicted risk. Tenure uses the employee SCD version valid on the exit date. Risk groups and tenure summaries are suppressed below five people or exits to protect privacy; individual risk scores are not shown.

- Dashboard: [`task_7/app.py`](task_7/app.py)
- Findings: [`task_7/evidence/findings.md`](task_7/evidence/findings.md)
- Dashboard notes: [`task_7/README.md`](task_7/README.md)

### Task 8 - Team productivity

Summarizes task delivery by team and sprint, with completed work, velocity, cycle time, blocked tasks, and reopened items. Cancelled tasks are excluded from active completion denominators. Interpret velocity with team size, sprint length, and work type rather than as a standalone team health score.

- Dashboard: [`task_8/app.py`](task_8/app.py)
- Manual verification: [`task_8/evidence/verification.md`](task_8/evidence/verification.md)
- Dashboard notes: [`task_8/README.md`](task_8/README.md)

### Task 9 - Payroll cost and reconciliation

Reports gross pay, net pay, employer cost, cost per employee, and monthly reconciliation against the supplied company-level answer key. Company totals do not validate department allocations. Payroll figures remain provisional pending Finance review: documented issues include duplicate employee/run rows, unmatched employee IDs, and five monthly differences. Source rows are preserved until Finance confirms any corrections.

- Dashboard: [`task_9/app.py`](task_9/app.py)
- Reconciliation notes: [`task_9/evidence/exclusions.md`](task_9/evidence/exclusions.md)
- Dashboard notes: [`task_9/README.md`](task_9/README.md)

### Task 10 - Budget and KPI targets

Builds budget and target metric views, then compares actuals with budget and KPI thresholds. Positive budget variance means overspend; percentage variance is divided by budget. Department actuals are shown only for groups with at least five employees. KPI status follows the supplied threshold direction, and missing values are labelled No data.

- Metric builder: [`task_10/build_metrics.py`](task_10/build_metrics.py)
- Dashboard: [`task_10/app.py`](task_10/app.py)
- Manual verification: [`task_10/evidence/verification.md`](task_10/evidence/verification.md)
- Dashboard notes: [`task_10/README.md`](task_10/README.md)

## Phase 2 evidence and outputs

The report records the five task outcomes, validation checks, and analysis limitations. Task-level evidence and screenshots are kept under each `task_6` through `task_10` folder. The dashboards passed local AppTest smoke checks and Python compile checks, with numeric spot checks documented in the task evidence.

Before using payroll results for decisions, complete Finance review of the documented differences and data-quality exceptions. For KPI and budget decisions, verify whether targets and budgets reflect the hiring freeze and current planning assumptions.
