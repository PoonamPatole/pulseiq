"""Build the PulseIQ star schema from Task 1 clean facts and raw dimensions."""

from __future__ import annotations

import re
from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"

DIMENSIONS = {
    "dim_account": ["account_code"],
    "dim_client": ["client_id"],
    "dim_date": ["date_key"],
    "dim_department": ["department_id"],
    "dim_employee": ["employee_key"],
    "dim_leave_type": ["leave_type_code"],
    "dim_location": ["work_location"],
    "dim_role": ["role_id"],
    "dim_sprint": ["sprint_id"],
    "dim_team": ["team_id"],
    "dim_vendor": ["vendor_id"],
}

FACTS = {
    "fact_payroll": ["payroll_item_id"],
    "fact_attendance_monthly": ["attendance_fact_id"],
    "fact_leave": ["leave_request_id"],
    "fact_headcount_monthly": ["date_key", "department_id"],
    "fact_ledger": ["line_id"],
    "fact_invoice": ["invoice_id"],
    "fact_invoice_payment": ["payment_id"],
    "fact_expense": ["expense_id"],
    "fact_task": ["task_id"],
    "fact_anomaly": ["result_id"],
    "fact_attrition_risk": ["prediction_id"],
    "fact_forecast": ["forecast_id"],
}


def source_for(con, table: str) -> str:
    exists = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='clean' AND table_name=?",
        [table],
    ).fetchone()[0]
    return f"clean.{table}" if exists else f"raw.{table}"


def qident(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")
    return f'"{identifier}"'


def as_of_employee_source(table: str, source: str) -> str:
    if table == "fact_task":
        return f"""
            SELECT f.*, d.employee_key
            FROM {source} AS f
            LEFT JOIN warehouse.dim_employee AS d
              ON d.employee_id = f.assignee_employee_id
             AND COALESCE(f.started_date, f.created_date) BETWEEN d.valid_from AND d.valid_to
        """
    if table == "fact_anomaly":
        return f"""
            SELECT f.*, d.employee_key
            FROM {source} AS f
            LEFT JOIN warehouse.dim_employee AS d
              ON d.employee_id = f.employee_id
             AND last_day(f.period) BETWEEN d.valid_from AND d.valid_to
        """
    return f"SELECT * FROM {source}"


def create_table_with_primary_key(con, schema: str, table: str, query: str, keys: list[str]) -> None:
    cols = con.execute(f"DESCRIBE SELECT * FROM ({query}) AS source_rows").fetchall()
    col_names = [row[0] for row in cols]
    missing_keys = sorted(set(keys) - set(col_names))
    if missing_keys:
        raise ValueError(f"{schema}.{table}: primary key columns not found: {missing_keys}")

    # Report bad keys before DuckDB's PRIMARY KEY constraint fails.
    qtable = f'"{schema}"."{table}"'
    null_predicate = " OR ".join(f'{qident(k)} IS NULL' for k in keys)
    key_select = ", ".join(qident(k) for k in keys)
    nulls = con.execute(
        f"SELECT COUNT(*) FROM ({query}) AS source_rows WHERE {null_predicate}"
    ).fetchone()[0]
    duplicates = con.execute(
        f"SELECT COUNT(*) FROM (SELECT {key_select} FROM ({query}) AS source_rows "
        f"GROUP BY {key_select} HAVING COUNT(*) > 1) AS duplicate_keys"
    ).fetchone()[0]
    if nulls or duplicates:
        raise ValueError(f"{schema}.{table}: {nulls} null key rows and {duplicates} duplicate keys")

    col_ddl = ", ".join(f"{qident(name)} {dtype}" for name, dtype, *_ in cols)
    pk_ddl = ", ".join(qident(k) for k in keys)
    con.execute(f"DROP TABLE IF EXISTS {qtable}")
    con.execute(f"CREATE TABLE {qtable} ({col_ddl}, PRIMARY KEY ({pk_ddl}))")
    con.execute(f"INSERT INTO {qtable} SELECT * FROM ({query}) AS source_rows")


def build_orphan_audit(con) -> None:
    con.execute("DROP TABLE IF EXISTS audit.orphan_rows")
    con.execute("""
        CREATE TABLE audit.orphan_rows (
            fact_table VARCHAR,
            row_key VARCHAR,
            relationship VARCHAR,
            key_value VARCHAR,
            reason VARCHAR
        )
    """)

    # Each check writes the offending fact row and a plain-language reason.
    checks = [
        ("fact_payroll", "payroll_item_id", "employee_key -> dim_employee", "employee_key", "dim_employee", "employee_key", "TRUE"),
        ("fact_payroll", "payroll_item_id", "date_key -> dim_date", "date_key", "dim_date", "date_key", "TRUE"),
        ("fact_payroll", "payroll_item_id", "department_id -> dim_department", "department_id", "dim_department", "department_id", "TRUE"),
        ("fact_payroll", "payroll_item_id", "role_id -> dim_role", "role_id", "dim_role", "role_id", "TRUE"),
        ("fact_attendance_monthly", "attendance_fact_id", "employee_key -> dim_employee", "employee_key", "dim_employee", "employee_key", "TRUE"),
        ("fact_attendance_monthly", "attendance_fact_id", "date_key -> dim_date", "date_key", "dim_date", "date_key", "TRUE"),
        ("fact_attendance_monthly", "attendance_fact_id", "department_id -> dim_department", "department_id", "dim_department", "department_id", "TRUE"),
        ("fact_leave", "leave_request_id", "employee_key -> dim_employee", "employee_key", "dim_employee", "employee_key", "TRUE"),
        ("fact_leave", "leave_request_id", "leave_type_code -> dim_leave_type", "leave_type_code", "dim_leave_type", "leave_type_code", "TRUE"),
        ("fact_leave", "leave_request_id", "start_date_key -> dim_date", "start_date_key", "dim_date", "date_key", "TRUE"),
        ("fact_leave", "leave_request_id", "end_date_key -> dim_date", "end_date_key", "dim_date", "date_key", "TRUE"),
        ("fact_headcount_monthly", "f.department_id || ':' || f.date_key", "department_id -> dim_department", "department_id", "dim_department", "department_id", "TRUE"),
        ("fact_headcount_monthly", "f.department_id || ':' || f.date_key", "date_key -> dim_date", "date_key", "dim_date", "date_key", "TRUE"),
        ("fact_ledger", "line_id", "account_code -> dim_account", "account_code", "dim_account", "account_code", "TRUE"),
        ("fact_ledger", "line_id", "cost_center_department_id -> dim_department", "cost_center_department_id", "dim_department", "department_id", "TRUE"),
        ("fact_ledger", "line_id", "date_key -> dim_date", "date_key", "dim_date", "date_key", "TRUE"),
        ("fact_invoice", "invoice_id", "client_id -> dim_client", "client_id", "dim_client", "client_id", "TRUE"),
        ("fact_invoice", "invoice_id", "service_line_account -> dim_account", "service_line_account", "dim_account", "account_code", "TRUE"),
        ("fact_invoice", "invoice_id", "invoice_date_key -> dim_date", "invoice_date_key", "dim_date", "date_key", "TRUE"),
        ("fact_invoice_payment", "payment_id", "invoice_id -> fact_invoice", "invoice_id", "fact_invoice", "invoice_id", "TRUE"),
        ("fact_invoice_payment", "payment_id", "payment_date_key -> dim_date", "payment_date_key", "dim_date", "date_key", "TRUE"),
        ("fact_expense", "expense_id", "vendor_id -> dim_vendor", "vendor_id", "dim_vendor", "vendor_id", "TRUE"),
        ("fact_expense", "expense_id", "category_account -> dim_account", "category_account", "dim_account", "account_code", "TRUE"),
        ("fact_expense", "expense_id", "department_id -> dim_department", "department_id", "dim_department", "department_id", "TRUE"),
        ("fact_expense", "expense_id", "expense_date_key -> dim_date", "expense_date_key", "dim_date", "date_key", "TRUE"),
        ("fact_task", "task_id", "team_id -> dim_team", "team_id", "dim_team", "team_id", "TRUE"),
        ("fact_task", "task_id", "sprint_id -> dim_sprint", "sprint_id", "dim_sprint", "sprint_id", "TRUE"),
        ("fact_task", "task_id", "assignee_employee_id at task date -> dim_employee", "employee_key", "dim_employee", "employee_key", "TRUE"),
        ("fact_anomaly", "result_id", "employee_id at period -> dim_employee", "employee_key", "dim_employee", "employee_key", "TRUE"),
        ("fact_anomaly", "result_id", "period_key -> dim_date", "period_key", "dim_date", "date_key", "TRUE"),
        ("fact_attrition_risk", "prediction_id", "employee_key -> dim_employee", "employee_key", "dim_employee", "employee_key", "TRUE"),
        ("fact_attrition_risk", "prediction_id", "department_id -> dim_department", "department_id", "dim_department", "department_id", "TRUE"),
        ("fact_attrition_risk", "prediction_id", "as_of_date_key -> dim_date", "as_of_date_key", "dim_date", "date_key", "TRUE"),
        ("fact_forecast", "forecast_id", "department_id -> dim_department (ALL exempt)", "department_id", "dim_department", "department_id", "f.department_id IS NULL OR f.department_id <> 'ALL'"),
        ("fact_forecast", "forecast_id", "forecast_month_key -> dim_date", "forecast_month_key", "dim_date", "date_key", "TRUE"),
    ]

    for fact, row_key, rel, key_col, target, target_key, applicable in checks:
        row_key_sql = row_key if row_key.startswith("f.") else f"f.{row_key}"
        if fact == "fact_task" and key_col == "employee_key":
            reason = "Assignee exists in dim_employee, but no SCD version is valid on the task date"
        elif fact == "fact_anomaly" and key_col == "employee_key":
            reason = "Employee exists in dim_employee, but no SCD version is valid at the anomaly month end"
        elif fact == "fact_forecast" and target == "dim_date":
            reason = "Forecast month is beyond the date dimension horizon supplied with the dataset"
        elif fact == "fact_payroll" and key_col == "employee_key":
            reason = "Source employee key does not exist in dim_employee (unknown-key sentinel or invalid source key)"
        elif fact == "fact_ledger" and key_col == "cost_center_department_id":
            reason = "No department is assigned to this ledger line; NULL is treated as an unallocated cost center"
        else:
            reason = "Referenced key is not present in the target dimension/table"
        if fact in {"fact_task", "fact_anomaly"} and key_col == "employee_key":
            missing_condition = "f.employee_key IS NULL"
        elif fact == "fact_ledger" and key_col == "cost_center_department_id":
            # A blank cost center is allowed for unallocated journal lines.
            missing_condition = f"f.{key_col} IS NOT NULL AND d.{target_key} IS NULL"
        else:
            missing_condition = f"d.{target_key} IS NULL"
        con.execute(f"""
            INSERT INTO audit.orphan_rows
            SELECT '{fact}', CAST({row_key_sql} AS VARCHAR), '{rel}', CAST(f.{key_col} AS VARCHAR),
                   '{reason}'
            FROM warehouse.{fact} f
            LEFT JOIN warehouse.{target} d ON f.{key_col} = d.{target_key}
            WHERE ({applicable}) AND ({missing_condition})
        """)


def main() -> None:
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}. Run python etl.py first.")
    con = duckdb.connect(str(DB_FILE))
    con.execute("CREATE SCHEMA IF NOT EXISTS warehouse")
    con.execute("CREATE SCHEMA IF NOT EXISTS audit")

    # Dimensions are copied from raw so their descriptive attributes and history remain intact.
    for table, keys in DIMENSIONS.items():
        create_table_with_primary_key(con, "warehouse", table, f"SELECT * FROM raw.{table}", keys)

    # Use Task 1 clean facts where available; otherwise preserve the source facts as loaded.
    for table, keys in FACTS.items():
        source = source_for(con, table)
        query = as_of_employee_source(table, source)
        create_table_with_primary_key(con, "warehouse", table, query, keys)

    build_orphan_audit(con)
    task1_rows = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT table_name, rows_passed, validation_status FROM audit.etl_summary"
    ).fetchall()}
    reconciliation = []
    for table in FACTS:
        warehouse_rows = con.execute(f"SELECT COUNT(*) FROM warehouse.{table}").fetchone()[0]
        if table in task1_rows:
            task1_passed, validation_status = task1_rows[table]
            status = ("RECONCILED" if warehouse_rows == task1_passed else "COUNT_MISMATCH")
            reconciliation.append((table, task1_passed, warehouse_rows,
                                   warehouse_rows == task1_passed, validation_status, status))
        else:
            reconciliation.append((table, None, warehouse_rows, None, "NO_TASK1_SUMMARY", "MISSING"))

    con.execute("DROP TABLE IF EXISTS audit.warehouse_reconciliation")
    con.execute("""
        CREATE TABLE audit.warehouse_reconciliation (
            fact_table VARCHAR,
            task1_rows_passed BIGINT,
            warehouse_rows BIGINT,
            reconciles BOOLEAN,
            validation_status VARCHAR,
            status VARCHAR
        )
    """)
    con.executemany("INSERT INTO audit.warehouse_reconciliation VALUES (?, ?, ?, ?, ?, ?)", reconciliation)

    print("Warehouse primary keys created for 11 dimensions and 12 facts.")
    print("\nTask 1 row-count reconciliation")
    print(con.execute("SELECT * FROM audit.warehouse_reconciliation ORDER BY fact_table").df().to_string(index=False))
    print("\nOrphan audit by relationship")
    print(con.execute("""
        SELECT fact_table, relationship, COUNT(*) AS orphan_rows
        FROM audit.orphan_rows
        GROUP BY fact_table, relationship
        ORDER BY fact_table, relationship
    """).df().to_string(index=False))
    orphan_count = con.execute("SELECT COUNT(*) FROM audit.orphan_rows").fetchone()[0]
    print(f"\nTotal orphan relationships recorded: {orphan_count}")
    con.close()


if __name__ == "__main__":
    main()
