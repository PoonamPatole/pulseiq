# Task 2 — Star-schema warehouse

Run these commands from the project root (with the project virtual environment active):

```powershell
python .\task_1\etl.py
python .\task_2\build_warehouse.py
```

The warehouse builder creates dimensions and facts with primary keys in the `warehouse` schema. It writes row-count reconciliation and row-level orphan explanations to the `audit` schema in the project-root `pulseiq.duckdb`. All 12 facts reconcile by row count; the audit distinguishes four detailed-contract feeds from eight feeds checked using dictionary type/nullability only.

Files:

- `build_warehouse.py` — Task 2 warehouse build and audit
- `docs/star_schema.md` — join map, Mermaid ER diagram, history rule, and audit findings
- `evidence/` — Task 2 output screenshot

The source data and starter files are shared under the root `data/` folder.

Use `evidence/reconciliation.md` for the current 12-fact reconciliation; the screenshot in this folder is an earlier partial run.
