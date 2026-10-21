# Task 3 — Data quality gatekeeper

## Run it

From the project root, load the feeds. Task 1 now records a successful-load timestamp and runs all 14 quality checks automatically:

```powershell
python .\task_1\etl.py
```

To prove the checks detect defects, run the scratch-only tests:

```powershell
python .\task_3\dq_gatekeeper.py --self-test
```

The tests clone source tables into a temporary `scratch` schema, inject one defect per check, verify that the bad-row count increases, and drop the scratch schema. They do not edit the raw or warehouse source tables.

## Results

The latest 14-row result set is `audit.dq_results` in the project-root `pulseiq.duckdb`. To display it:

```powershell
python -c "import duckdb; c=duckdb.connect(r'pulseiq.duckdb', read_only=True); print(c.sql('SELECT check_id, check_name, severity, bad_rows, status FROM audit.dq_results ORDER BY check_id').df().to_string(index=False))"
```

`FAIL` means a Critical check found a problem and the gatekeeper returns a failing exit code. `WARN` means a Warning check found a problem but does not stop the run. `PASS` means no bad rows were returned.

The current supplied data produces five Critical checks with findings. Therefore `etl.py` exits with code 1 after loading and recording the result set. This is the intended gate response: the load is recorded, but downstream promotion should wait until the Critical findings are resolved or formally accepted. The raw tables are preserved for investigation; the gate does not silently delete rows.

Check meanings and stop/warn decisions are in `docs/check_explanations.md`. The planted-issue comparison belongs in `docs/missed_issues.md` after the authorized PQ-03 validation file is available.
