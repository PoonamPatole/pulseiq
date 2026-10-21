# Task 1 — Raw loading and contract validation

Run these commands from the project root (with the project virtual environment active):

```powershell
python .\task_1\check_row_counts.py
python .\task_1\etl.py
python .\task_1\verify_rerun.py
```

`check_row_counts.py` compares all CSV row counts with the DuckDB `raw` tables. `etl.py` reloads the CSVs, validates every fact column, writes clean/quarantine/summary tables and a successful-load log to the project-root `pulseiq.duckdb`, then automatically runs the Task 3 quality gatekeeper. Four feeds use the supplied detailed contracts; all fact columns also use the supplied dictionary's type and nullability. The other eight have no supplied allowed-value/business-rule rules, so those are not invented.

`verify_rerun.py` runs the pipeline twice and compares row counts and row contents across raw, clean, summary, and quarantine tables. The current data has Critical DQ findings, so each run may correctly exit with code 1 after saving its outputs; the rerun verifier treats that known gate result as expected and separately confirms the ETL tables remain stable.

Files:

- `etl.py` — Task 1 loader and validator
- `check_row_counts.py` — CSV-to-database count check
- `contract_notes.md` — notes for three contracted feeds
- `evidence/` — Task 1 output screenshot

The source data and starter files are shared under the root `data/` folder.

See `evidence/current_run.md` for the latest summary and `verify_rerun.py` for the idempotency check. `dictionary_contracts.py` applies the dictionary's fact-column types and nullability where detailed business rules were not supplied.
