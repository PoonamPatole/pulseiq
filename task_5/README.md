# Task 5 — Workforce and headcount dashboard

## Run it

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe .\task_4\create_metric_views.py
.\.venv\Scripts\python.exe .\task_5\build_workforce_metrics.py
.\.venv\Scripts\python.exe -m streamlit run .\task_5\app.py
```

Streamlit opens the dashboard in your browser. Use the sidebar to filter department and month range. The second page, **CEO Questions**, lists the five questions and metric/privacy notes.

The dashboard also displays M29, a month-over-month headcount-growth metric added for the Phase 1 mini-challenge. Its definition and calculator check are in `docs/mini_challenge.md`.

## Data and privacy

The app reads only `metrics.*` views. The setup script creates aggregate views from the Task 2 warehouse for department labels, city tier, and work mode; the app never queries raw or warehouse tables. Groups below the applicable threshold are suppressed. If you change the metric definitions, rerun both setup scripts before opening the app.

The company headcount card uses a company-level aggregate so small department groups are not lost by summing suppressed departmental cells. Department and composition breakdowns show reportable groups only.

The current training data has unresolved Task 3 quality findings. Payroll is not used on this page; treat headcount-derived metrics as provisional until the relevant quality checks pass.

## Evidence

Save a screenshot from the browser in `task_5/evidence/` after running the app. The five CEO questions and colour key are in `docs/ceo_questions.md`.
