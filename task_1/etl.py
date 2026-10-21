"""Validate the contract-backed feeds and write clean, quarantine, and audit tables.

Run from the project root with: python .\\task_1\\etl.py
The provided data_contracts file defines contracts for fact_anomaly,
fact_attrition_risk, fact_forecast, and fact_task only. Other raw fact tables
remain untouched and are marked as row-count-only, not contract-validated.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date, datetime, timezone
from numbers import Integral, Real
from pathlib import Path

import duckdb
import pandas as pd
from dictionary_contracts import inferred_fact_contracts


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "03_Data"
CONTRACT_FILE = DATA_DIR / "csv" / "data_contracts.csv"
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"
CSV_DIR = DATA_DIR / "csv"


def is_empty(value) -> bool:
    if value is None:
        return True
    try:
        if bool(pd.isna(value)):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value == ""


def matches_type(value, declared_type: str) -> bool:
    kind = declared_type.strip().lower()
    if kind in {"string", "char(1)"}:
        return isinstance(value, str)
    if kind in {"text", "varchar"}:
        return isinstance(value, str)
    if kind in {"int", "integer"}:
        if isinstance(value, Integral) and not isinstance(value, bool):
            return True
        return isinstance(value, Real) and not isinstance(value, bool) and float(value).is_integer()
    if kind.startswith("decimal") or kind in {"float", "double", "numeric"}:
        return isinstance(value, Real) and not isinstance(value, bool)
    if kind == "date":
        # DuckDB's pandas export represents DATE values as pandas.Timestamp.
        return isinstance(value, date)
    if kind == "timestamp":
        return isinstance(value, datetime)
    if kind in {"boolean", "bool"}:
        return isinstance(value, bool)
    return True  # Unknown contract type: preserve the row and flag the schema below.


def violations_for(table: str, row: dict, contracts: list[dict]) -> list[str]:
    problems = []

    for contract in contracts:
        column = contract["column_name"]
        dtype = contract["data_type"]
        nullable = contract["nullable"].strip().lower() == "yes"
        rule = contract["rule_or_allowed_values"].strip()
        value = row.get(column)

        if is_empty(value):
            if not nullable:
                problems.append(f"{column}: required value is empty")
            continue

        if not matches_type(value, dtype):
            problems.append(f"{column}: expected {dtype}")
            continue

        # Explicit enumerations in the supplied contracts.
        pipe_values = [part.strip() for part in rule.split("|")]
        if len(pipe_values) > 1 and all(re.fullmatch(r"[A-Za-z0-9_ -]+", x) for x in pipe_values):
            if str(value) not in pipe_values:
                problems.append(f"{column}: value {value!r} is outside {rule}")
        elif rule == "1,2,3,5,8,13" and value not in {1, 2, 3, 5, 8, 13}:
            problems.append(f"{column}: value must be one of 1, 2, 3, 5, 8, 13")
        elif rule == "P1..P4" and value not in {"P1", "P2", "P3", "P4"}:
            problems.append(f"{column}: value must be P1, P2, P3, or P4")

        # Contract constraints that can be checked from one row.
        if "0 to 1" in rule and not 0 <= value <= 1:
            problems.append(f"{column}: value must be between 0 and 1")
        if rule == ">= 0" and value < 0:
            problems.append(f"{column}: value must be >= 0")
        if rule == ">= forecast_value" and value < row["forecast_value"]:
            problems.append(f"{column}: must be >= forecast_value")
        if rule == "<= forecast_value" and value > row["forecast_value"]:
            problems.append(f"{column}: must be <= forecast_value")
        if rule == "unique, format AN-nnnn" and not re.fullmatch(r"AN-\d{4}", str(value)):
            problems.append(f"{column}: expected format AN-nnnn")
        if rule == "unique AR-nnnn" and not re.fullmatch(r"AR-\d{4}", str(value)):
            problems.append(f"{column}: expected format AR-nnnn")
        if rule == "unique FC-nnnn" and not re.fullmatch(r"FC-\d{4}", str(value)):
            problems.append(f"{column}: expected format FC-nnnn")
        if rule == "unique TASK-nnnnn" and not re.fullmatch(r"TASK-\d{5}", str(value)):
            problems.append(f"{column}: expected format TASK-nnnnn")
        if column == "trained_through" and not re.fullmatch(r"\d{4}-\d{2}", str(value)):
            problems.append(f"{column}: expected YYYY-MM")
        if column == "forecast_month" and value.day != 1:
            problems.append(f"{column}: must be the first day of the month")

    # Cross-column rules in the supplied task-board contract.
    if table == "fact_task":
        created, started, due, completed = (row.get(c) for c in
                                             ("created_date", "started_date", "due_date", "completed_date"))
        status = row.get("status")
        if not is_empty(created) and not is_empty(started) and created > started:
            problems.append("created_date: must be <= started_date")
        if is_empty(started) and status != "To Do":
            problems.append("started_date: blank is allowed only when status is To Do")
        if status == "Done" and is_empty(completed):
            problems.append("completed_date: required when status is Done")
        if not is_empty(completed) and not is_empty(started) and completed < started:
            problems.append("completed_date: must be >= started_date")

    if table == "fact_anomaly" and row.get("source_dataset") == "attendance_monthly_features":
        if not is_empty(row.get("money_at_risk")):
            problems.append("money_at_risk: must be blank for attendance rows")

    return problems


def main() -> None:
    contracts_df = pd.read_csv(CONTRACT_FILE, keep_default_na=False)
    contracts_by_table = {}
    official_contract_tables = set()
    for _, contract in contracts_df.iterrows():
        match = re.search(r"\((fact_[a-z0-9_]+)\)", contract["feed"])
        if match:
            official_contract_tables.add(match.group(1))
            item = contract.to_dict()
            # The source sheet uses this shorthand to describe three real columns.
            columns = (["top_reason_1", "top_reason_2", "top_reason_3"]
                       if item["column_name"] == "top_reason_1..3" else [item["column_name"]])
            for column in columns:
                expanded = dict(item)
                expanded["column_name"] = column
                expanded["contract_source"] = "data_contracts"
                contracts_by_table.setdefault(match.group(1), []).append(expanded)

    # The starter contracts provide detailed rules for four feeds. For every
    # other fact column (and extra columns on those four feeds), apply the
    # supplied dictionary's declared type and observed nullability. Never infer
    # allowed values from the current data.
    dictionary_contracts = inferred_fact_contracts(str(DATA_DIR / "csv" / "data_dictionary.csv"))
    dictionary_checked_tables = set()
    for table, inferred_columns in dictionary_contracts.items():
        existing = {item["column_name"] for item in contracts_by_table.get(table, [])}
        additions = [item for item in inferred_columns if item["column_name"] not in existing]
        if additions:
            contracts_by_table.setdefault(table, []).extend(additions)
            dictionary_checked_tables.add(table)

    con = duckdb.connect(str(DB_FILE))
    con.execute("CREATE SCHEMA IF NOT EXISTS clean")
    con.execute("CREATE SCHEMA IF NOT EXISTS audit")
    run_started_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Reload every supplied CSV into raw on each run. This makes `python etl.py`
    # the single repeatable command for both loading and validating the feeds.
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for csv_file in sorted(CSV_DIR.glob("*.csv")):
        table = csv_file.stem
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
            raise ValueError(f"Unexpected CSV filename for a table: {csv_file.name}")
        csv_path = str(csv_file).replace("'", "''")
        con.execute(f"CREATE OR REPLACE TABLE raw.{table} AS "
                    f"SELECT * FROM read_csv_auto('{csv_path}', header=true)")
        row_count = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        print(f"Loaded raw.{table:<32}{row_count:>8} rows")

    summary = []

    for table, contracts in sorted(contracts_by_table.items()):
        source_cols = [r[0] for r in con.execute(f"DESCRIBE raw.{table}").fetchall()]
        contract_cols = [c["column_name"] for c in contracts]
        missing = sorted(set(contract_cols) - set(source_cols))
        extra = sorted(set(source_cols) - set(contract_cols))
        if missing:
            raise ValueError(f"{table}: contract columns missing from raw table: {missing}")
        if extra:
            # Keep the complete source row, and make schema drift visible in the summary.
            print(f"WARNING {table}: source has columns without a contract: {', '.join(extra)}")

        raw_rows = con.execute(f"SELECT * FROM raw.{table}").fetchdf().to_dict("records")
        # Precompute reference keys for the contracts' 'exists in dimension' rules.
        ref_sets = {}
        for ref_table, ref_col in [("dim_employee", "employee_id"), ("dim_department", "department_id"),
                                   ("dim_team", "team_id"), ("dim_sprint", "sprint_id")]:
            try:
                ref_sets[(ref_table, ref_col)] = set(
                    r[0] for r in con.execute(f"SELECT {ref_col} FROM raw.{ref_table}").fetchall()
                )
            except Exception:
                ref_sets[(ref_table, ref_col)] = set()

        good, bad = [], []
        seen = {c["column_name"]: set() for c in contracts if "unique" in c["rule_or_allowed_values"]}
        for row in raw_rows:
            # CSV type inference can load numeric-looking identifiers as
            # numbers even when the dictionary promises text (for example
            # account codes). Preserve raw unchanged; normalize only clean-row
            # values before applying the declared type.
            for contract in contracts:
                column = contract["column_name"]
                value = row.get(column)
                if (not is_empty(value)
                        and contract["data_type"].strip().lower() in {"string", "text", "varchar"}
                        and isinstance(value, Real) and not isinstance(value, bool)):
                    row[column] = str(int(value)) if float(value).is_integer() else str(value)
            reasons = violations_for(table, row, contracts)
            for c in contracts:
                col, rule = c["column_name"], c["rule_or_allowed_values"]
                if "unique" in rule and row.get(col) is not None:
                    if row[col] in seen[col]:
                        reasons.append(f"{col}: duplicate value {row[col]!r}")
                    seen[col].add(row[col])
                ref = None
                if "exists in dim_employee" in rule:
                    ref = ("dim_employee", "employee_id")
                elif "exists in dim_department" in rule:
                    ref = ("dim_department", "department_id")
                elif "exists in dim_team" in rule:
                    ref = ("dim_team", "team_id")
                elif "exists in dim_sprint" in rule:
                    ref = ("dim_sprint", "sprint_id")
                if ref and row.get(col) is not None and row[col] not in ref_sets[ref]:
                    reasons.append(f"{col}: {row[col]!r} does not exist in raw.{ref[0]}")
            if reasons:
                row["etl_reason"] = "; ".join(reasons)
                bad.append(row)
            else:
                good.append(row)

        # CREATE OR REPLACE makes each run a fresh snapshot, so a rerun cannot append duplicates.
        con.execute(f"CREATE OR REPLACE TABLE clean.{table} AS SELECT * FROM raw.{table} WHERE FALSE")
        if good:
            con.register("good_rows", pd.DataFrame(good, columns=source_cols))
            con.execute(f"INSERT INTO clean.{table} SELECT * FROM good_rows")
            con.unregister("good_rows")
        if bad:
            bad_df = pd.DataFrame(bad)
        else:
            bad_df = pd.DataFrame(columns=source_cols + ["etl_reason"])
        con.execute(f"CREATE OR REPLACE TABLE audit.{table}_quarantine AS "
                    f"SELECT *, CAST(NULL AS VARCHAR) AS etl_reason FROM raw.{table} WHERE FALSE")
        if bad:
            con.register("bad_rows", bad_df)
            con.execute(f"INSERT INTO audit.{table}_quarantine SELECT * FROM bad_rows")
            con.unregister("bad_rows")

        validation_status = ("CONTRACT_AND_DICTIONARY_VALIDATED" if table in official_contract_tables
                             else "DICTIONARY_SCHEMA_VALIDATED")
        summary.append({"table_name": table, "rows_in": len(raw_rows), "rows_passed": len(good),
                        "rows_quarantined": len(bad), "uncontracted_columns": ", ".join(extra),
                        "validation_status": validation_status})

    raw_facts = {r[0] for r in con.execute("SHOW TABLES FROM raw").fetchall() if r[0].startswith("fact_")}
    uncovered_facts = raw_facts - set(contracts_by_table)
    if uncovered_facts:
        raise ValueError(f"No contract or dictionary schema found for raw facts: {sorted(uncovered_facts)}")
    print("Dictionary-based fact checks validate declared type and nullability only; no allowed-value lists are inferred.")

    summary_df = pd.DataFrame(summary)
    con.register("summary_rows", summary_df)
    con.execute("CREATE OR REPLACE TABLE audit.etl_summary AS SELECT * FROM summary_rows")
    con.unregister("summary_rows")
    print("\nContract validation summary")
    print(con.execute("SELECT table_name, rows_in, rows_passed, rows_quarantined, validation_status, uncontracted_columns "
                      "FROM audit.etl_summary ORDER BY table_name").df().to_string(index=False))
    run_finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
    run_id = run_finished_at.strftime("etl_%Y%m%dT%H%M%S%fZ")
    con.execute("""
        CREATE TABLE IF NOT EXISTS audit.etl_run_log (
            run_id VARCHAR,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            status VARCHAR
        )
    """)
    con.execute("INSERT INTO audit.etl_run_log VALUES (?, ?, ?, 'SUCCESS')",
                [run_id, run_started_at, run_finished_at])
    con.close()

    # Run the quality gate automatically after each successful raw load.
    gatekeeper = PROJECT_DIR / "task_3" / "dq_gatekeeper.py"
    if gatekeeper.exists():
        sys.stdout.flush()
        result = subprocess.run([sys.executable, str(gatekeeper)], check=False)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
