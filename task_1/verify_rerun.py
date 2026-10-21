"""Run Task 1 twice and verify its materialized outputs stay unchanged."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"
ETL_FILE = PROJECT_DIR / "task_1" / "etl.py"


def snapshot() -> dict[str, tuple[int, str]]:
    con = duckdb.connect(str(DB_FILE), read_only=True)
    try:
        names = con.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE (table_schema = 'raw' OR table_schema = 'clean'
                   OR (table_schema = 'audit' AND
                       (table_name = 'etl_summary' OR table_name LIKE '%_quarantine')))
            ORDER BY table_schema, table_name
        """).fetchall()
        result = {}
        for schema, table in names:
            full_name = f'{schema}.{table}'
            count = con.execute(f"SELECT COUNT(*) FROM {full_name}").fetchone()[0]
            rows = con.execute(f"SELECT * FROM {full_name} ORDER BY ALL").fetchall()
            digest = hashlib.sha256(repr(rows).encode("utf-8")).hexdigest()
            result[full_name] = (count, digest)
        return result
    finally:
        con.close()


def run_pipeline(run_number: int) -> int:
    result = subprocess.run(
        [sys.executable, str(ETL_FILE)], cwd=PROJECT_DIR,
        capture_output=True, text=True, check=False,
    )
    print(f"Task 1 run {run_number}: exit {result.returncode}")
    if result.returncode not in (0, 1):
        print(result.stdout[-3000:])
        print(result.stderr[-3000:])
        raise SystemExit(f"Unexpected ETL error on run {run_number}")
    # Exit 1 is expected while the supplied dataset has Critical DQ findings.
    return result.returncode


def main() -> None:
    run_pipeline(1)
    first = snapshot()
    run_pipeline(2)
    second = snapshot()
    if first != second:
        changed = sorted(name for name in first.keys() | second.keys()
                         if first.get(name) != second.get(name))
        raise SystemExit(f"Task 1 outputs changed after rerun: {changed}")
    print(f"PASS: {len(second)} raw, clean, summary, and quarantine tables have stable rows and contents.")
    print("The audit.etl_run_log and audit.dq_results are run-history outputs and intentionally change per run.")


if __name__ == "__main__":
    main()
