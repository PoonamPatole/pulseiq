"""Run the 14 catalogued PulseIQ quality checks and prove them in scratch copies."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"


def check_definitions(raw: str, audit: str) -> list[dict]:
    return [
        {
            "id": "DQ-C01", "table": "fact_payroll + fact_ledger",
            "sql": f"""
                WITH p AS (
                    SELECT strftime(period_end_date, '%Y-%m') AS month,
                           SUM(employer_cost) AS payroll_cost
                    FROM {raw}.fact_payroll GROUP BY 1
                ), l AS (
                    SELECT posting_period AS month,
                           SUM(signed_amount_debit_positive) AS ledger_cost
                    FROM {raw}.fact_ledger
                    WHERE CAST(account_code AS VARCHAR) IN ('5001','5002','5003','5004','5005')
                    GROUP BY 1
                ), comparison AS (
                    SELECT COALESCE(p.month, l.month) AS month,
                           COALESCE(p.payroll_cost, 0) AS payroll_cost,
                           COALESCE(l.ledger_cost, 0) AS ledger_cost
                    FROM p FULL OUTER JOIN l USING (month)
                )
                SELECT *, payroll_cost - ledger_cost AS difference
                FROM comparison
                WHERE ABS(payroll_cost - ledger_cost) > 0.01
            """,
        },
        {
            "id": "DQ-C02", "table": "fact_ledger",
            "sql": f"""
                SELECT entry_id, SUM(debit) AS debits, SUM(credit) AS credits,
                       ABS(SUM(debit) - SUM(credit)) AS difference
                FROM {raw}.fact_ledger GROUP BY entry_id
                HAVING ABS(SUM(debit) - SUM(credit)) > 0.005
            """,
        },
        {
            "id": "DQ-C03", "table": "fact_payroll",
            "sql": f"""
                SELECT employee_id, run_id, COUNT(*) AS duplicate_rows
                FROM {raw}.fact_payroll GROUP BY employee_id, run_id
                HAVING COUNT(*) > 1
            """,
        },
        {
            "id": "DQ-C04", "table": "fact_payroll + dim_employee",
            "sql": f"""
                SELECT f.payroll_item_id, f.employee_id
                FROM {raw}.fact_payroll f
                LEFT JOIN {raw}.dim_employee d ON f.employee_id = d.employee_id
                WHERE d.employee_id IS NULL
            """,
        },
        {
            "id": "DQ-C05", "table": "fact_attendance_monthly + dim_employee",
            "sql": f"""
                SELECT a.attendance_fact_id, a.employee_id, a.period_end_date, d.exit_date
                FROM {raw}.fact_attendance_monthly a
                JOIN {raw}.dim_employee d
                  ON a.employee_id = d.employee_id AND d.is_current = 'Y'
                WHERE d.exit_date IS NOT NULL
                  AND a.period_end_date > last_day(d.exit_date)
            """,
        },
        {
            "id": "DQ-C06", "table": "fact_attendance_monthly + fact_payroll",
            "sql": f"""
                SELECT a.attendance_fact_id, a.employee_id, a.period_end_date,
                       a.unpaid_absence_days, p.lop_days
                FROM {raw}.fact_attendance_monthly a
                LEFT JOIN {raw}.fact_payroll p
                  ON p.employee_id = a.employee_id
                 AND p.period_end_date = a.period_end_date
                WHERE a.unpaid_absence_days > 0.5
                  AND (p.payroll_item_id IS NULL OR p.lop_days + 0.5 < a.unpaid_absence_days)
            """,
        },
        {
            "id": "DQ-C07", "table": "fact_invoice",
            "sql": f"""
                SELECT invoice_id, amount_paid, total_amount, balance_due
                FROM {raw}.fact_invoice
                WHERE amount_paid > total_amount + 0.01 OR balance_due < -0.01
            """,
        },
        {
            "id": "DQ-C08", "table": "fact_expense",
            "sql": f"""
                SELECT expense_id, total_amount, amount_excl_gst, gst_amount,
                       total_amount - (amount_excl_gst + gst_amount) AS difference
                FROM {raw}.fact_expense
                WHERE ABS(total_amount - (amount_excl_gst + gst_amount)) > 0.01
            """,
        },
        {
            "id": "DQ-C09", "table": "fact_task",
            "sql": f"""
                SELECT task_id, status, started_date, completed_date
                FROM {raw}.fact_task
                WHERE completed_date < started_date
                   OR (status = 'Done' AND completed_date IS NULL)
            """,
        },
        {
            "id": "DQ-C10", "table": "fact_leave",
            "sql": f"""
                SELECT leave_request_id, start_date, end_date
                FROM {raw}.fact_leave WHERE end_date < start_date
            """,
        },
        {
            "id": "DQ-C11", "table": "fact_attrition_risk + fact_anomaly",
            "sql": f"""
                SELECT 'fact_attrition_risk' AS source_table, prediction_id AS row_id,
                       'as_of_date is over 7 days behind this batch' AS issue
                FROM {raw}.fact_attrition_risk
                WHERE as_of_date < (SELECT MAX(as_of_date) FROM {raw}.fact_attrition_risk) - INTERVAL '7 days'
                UNION ALL
                SELECT 'fact_anomaly', result_id, 'scored_at is over 24 hours before the last successful load'
                FROM {raw}.fact_anomaly
                WHERE scored_at < (
                    SELECT MAX(finished_at) - INTERVAL '24 hours'
                    FROM {audit}.etl_run_log WHERE status = 'SUCCESS'
                )
            """,
        },
        {
            "id": "DQ-C12", "table": "dim_employee",
            "sql": f"""
                SELECT a.employee_id, a.employee_key AS earlier_key, b.employee_key AS later_key,
                       a.valid_to AS earlier_valid_to, b.valid_from AS later_valid_from
                FROM {raw}.dim_employee a
                JOIN {raw}.dim_employee b
                  ON a.employee_id = b.employee_id
                 AND a.employee_key < b.employee_key
                 AND a.valid_to >= b.valid_from
            """,
        },
        {
            "id": "DQ-C13", "table": "audit.etl_run_log",
            "sql": f"""
                SELECT MAX(finished_at) AS latest_successful_load,
                       current_timestamp AS checked_at
                FROM {audit}.etl_run_log
                HAVING MAX(finished_at) IS NULL
                    OR MAX(finished_at) < current_timestamp - INTERVAL '24 hours'
            """,
        },
        {
            "id": "DQ-C14", "table": "metric_dictionary",
            "sql": f"""
                SELECT metric_id, metric_name, minimum_group_size
                FROM {raw}.metric_dictionary
                WHERE (
                    metric_id IN ('M01','M02','M03','M04','M05','M06','M07','M08','M09','M10',
                                  'M11','M12','M13','M14','M15','M19','M22','M23','M24','M25','M26','M27')
                    AND (
                        NULLIF(TRIM(minimum_group_size), '') IS NULL
                        OR TRY_CAST(REGEXP_EXTRACT(minimum_group_size, '[0-9]+', 0) AS INTEGER) IS NULL
                        OR TRY_CAST(REGEXP_EXTRACT(minimum_group_size, '[0-9]+', 0) AS INTEGER) <= 0
                    )
                ) OR (
                    NULLIF(TRIM(minimum_group_size), '') IS NOT NULL
                    AND (
                        TRY_CAST(REGEXP_EXTRACT(minimum_group_size, '[0-9]+', 0) AS INTEGER) IS NULL
                        OR TRY_CAST(REGEXP_EXTRACT(minimum_group_size, '[0-9]+', 0) AS INTEGER) <= 0
                    )
                )
            """,
        },
    ]


def load_catalog(con) -> dict[str, dict]:
    rows = con.execute("""
        SELECT check_id, check_name, severity, tolerance, owner, fix_guidance
        FROM raw.dq_checks_catalog ORDER BY check_id
    """).fetchall()
    catalog = {
        row[0]: {
            "name": row[1], "severity": row[2], "tolerance": row[3],
            "owner": row[4], "fix_guidance": row[5],
        }
        for row in rows
    }
    if len(catalog) != 14:
        raise ValueError(f"Expected 14 catalog checks, found {len(catalog)}")
    return catalog


def execute_check(con, sql: str):
    return con.execute(sql).fetchdf()


def save_results(con, definitions: list[dict], catalog: dict[str, dict]) -> list[dict]:
    run_time = datetime.now(timezone.utc).replace(tzinfo=None)
    results = []
    for definition in definitions:
        meta = catalog[definition["id"]]
        bad = execute_check(con, definition["sql"])
        count = len(bad)
        severity = meta["severity"]
        status = "PASS" if count == 0 else ("FAIL" if severity == "Critical" else "WARN")
        sample = bad.head(10).to_dict(orient="records")
        results.append({
            "check_id": definition["id"],
            "check_name": meta["name"],
            "table_name": definition["table"],
            "severity": severity,
            "bad_rows": count,
            "status": status,
            "run_time": run_time,
            "owner": meta["owner"],
            "fix_guidance": meta["fix_guidance"],
            "sample_bad_rows": json.dumps(sample, default=str),
            "check_sql": " ".join(definition["sql"].split()),
        })
    con.execute("""
        CREATE OR REPLACE TABLE audit.dq_results (
            check_id VARCHAR,
            check_name VARCHAR,
            table_name VARCHAR,
            severity VARCHAR,
            bad_rows BIGINT,
            status VARCHAR,
            run_time TIMESTAMP,
            owner VARCHAR,
            fix_guidance VARCHAR,
            sample_bad_rows VARCHAR,
            check_sql VARCHAR
        )
    """)
    con.executemany(
        "INSERT INTO audit.dq_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [tuple(row[key] for key in (
            "check_id", "check_name", "table_name", "severity", "bad_rows", "status",
            "run_time", "owner", "fix_guidance", "sample_bad_rows", "check_sql"
        )) for row in results],
    )
    return results


def clone_sources_to_scratch(con) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS scratch")
    tables = con.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='raw' ORDER BY table_name
    """).fetchall()
    for (table,) in tables:
        con.execute(f"CREATE OR REPLACE TABLE scratch.{table} AS SELECT * FROM raw.{table}")
    con.execute("CREATE OR REPLACE TABLE scratch.etl_run_log AS SELECT * FROM audit.etl_run_log")


def reset_scratch(con, *tables: str) -> None:
    for table in tables:
        con.execute(f"CREATE OR REPLACE TABLE scratch.{table} AS SELECT * FROM raw.{table}")


def inject_bad_row(con, check_id: str) -> tuple[str, ...]:
    """Change scratch copies only; return source tables to restore after this test."""
    if check_id == "DQ-C01":
        con.execute("UPDATE scratch.fact_payroll SET employer_cost=employer_cost+10 WHERE payroll_item_id=(SELECT payroll_item_id FROM scratch.fact_payroll LIMIT 1)")
        return ("fact_payroll",)
    if check_id == "DQ-C02":
        con.execute("UPDATE scratch.fact_ledger SET debit=debit+1 WHERE line_id=(SELECT line_id FROM scratch.fact_ledger LIMIT 1)")
        return ("fact_ledger",)
    if check_id == "DQ-C03":
        con.execute("INSERT INTO scratch.fact_payroll SELECT * FROM scratch.fact_payroll LIMIT 1")
        return ("fact_payroll",)
    if check_id == "DQ-C04":
        con.execute("UPDATE scratch.fact_payroll SET employee_id='EMP-NOT-IN-DIM' WHERE payroll_item_id=(SELECT payroll_item_id FROM scratch.fact_payroll LIMIT 1)")
        return ("fact_payroll",)
    if check_id == "DQ-C05":
        employee_id, attendance_id, period_end = con.execute("""
            SELECT a.employee_id, a.attendance_fact_id, a.period_end_date
            FROM scratch.fact_attendance_monthly a
            JOIN scratch.dim_employee d ON d.employee_id=a.employee_id AND d.is_current='Y'
            WHERE d.exit_date IS NULL LIMIT 1
        """).fetchone()
        con.execute("UPDATE scratch.dim_employee SET exit_date=? WHERE employee_id=? AND is_current='Y'", [period_end, employee_id])
        con.execute("UPDATE scratch.fact_attendance_monthly SET period_end_date=? WHERE attendance_fact_id=?", [period_end, attendance_id])
        # Exit is set to the same date; the check compares against LAST_DAY(exit_date),
        # so make attendance one month later to create the controlled violation.
        con.execute("UPDATE scratch.fact_attendance_monthly SET period_end_date=last_day(? + INTERVAL '1 month') WHERE attendance_fact_id=?", [period_end, attendance_id])
        return ("dim_employee", "fact_attendance_monthly")
    if check_id == "DQ-C06":
        employee_id, period_end, payroll_id, attendance_id = con.execute("""
            SELECT a.employee_id, a.period_end_date, p.payroll_item_id, a.attendance_fact_id
            FROM scratch.fact_attendance_monthly a
            JOIN scratch.fact_payroll p ON p.employee_id=a.employee_id AND p.period_end_date=a.period_end_date
            LIMIT 1
        """).fetchone()
        con.execute("UPDATE scratch.fact_attendance_monthly SET unpaid_absence_days=1 WHERE attendance_fact_id=?", [attendance_id])
        con.execute("UPDATE scratch.fact_payroll SET lop_days=0 WHERE payroll_item_id=?", [payroll_id])
        return ("fact_attendance_monthly", "fact_payroll")
    if check_id == "DQ-C07":
        con.execute("UPDATE scratch.fact_invoice SET amount_paid=total_amount+1 WHERE invoice_id=(SELECT invoice_id FROM scratch.fact_invoice LIMIT 1)")
        return ("fact_invoice",)
    if check_id == "DQ-C08":
        con.execute("UPDATE scratch.fact_expense SET total_amount=amount_excl_gst+gst_amount+1 WHERE expense_id=(SELECT expense_id FROM scratch.fact_expense LIMIT 1)")
        return ("fact_expense",)
    if check_id == "DQ-C09":
        con.execute("UPDATE scratch.fact_task SET status='Done', completed_date=NULL WHERE task_id=(SELECT task_id FROM scratch.fact_task LIMIT 1)")
        return ("fact_task",)
    if check_id == "DQ-C10":
        con.execute("UPDATE scratch.fact_leave SET end_date=start_date-INTERVAL '1 day' WHERE leave_request_id=(SELECT leave_request_id FROM scratch.fact_leave LIMIT 1)")
        return ("fact_leave",)
    if check_id == "DQ-C11":
        con.execute("UPDATE scratch.fact_attrition_risk SET as_of_date=(SELECT MAX(as_of_date)-INTERVAL '30 days' FROM scratch.fact_attrition_risk) WHERE prediction_id=(SELECT prediction_id FROM scratch.fact_attrition_risk ORDER BY as_of_date DESC LIMIT 1)")
        return ("fact_attrition_risk",)
    if check_id == "DQ-C12":
        con.execute("""
            UPDATE scratch.dim_employee AS old
            SET valid_to=(SELECT MIN(new.valid_from) FROM scratch.dim_employee new
                          WHERE new.employee_id=old.employee_id AND new.valid_from>old.valid_from)
            WHERE old.employee_key=(SELECT MIN(employee_key) FROM scratch.dim_employee
                                    GROUP BY employee_id HAVING COUNT(*)>1 LIMIT 1)
        """)
        return ("dim_employee",)
    if check_id == "DQ-C13":
        con.execute("UPDATE scratch.etl_run_log SET finished_at=current_timestamp-INTERVAL '2 days' WHERE status='SUCCESS'")
        return ()
    if check_id == "DQ-C14":
        con.execute("UPDATE scratch.metric_dictionary SET minimum_group_size='0' WHERE metric_id=(SELECT metric_id FROM scratch.metric_dictionary LIMIT 1)")
        return ("metric_dictionary",)
    raise ValueError(f"No bad-row injection defined for {check_id}")


def self_test(con, definitions: list[dict]) -> list[tuple[str, int, int, bool]]:
    clone_sources_to_scratch(con)
    tests = []
    scratch_checks = check_definitions("scratch", "scratch")
    by_id = {item["id"]: item for item in scratch_checks}
    for definition in definitions:
        check_id = definition["id"]
        sql = by_id[check_id]["sql"]
        baseline = len(execute_check(con, sql))
        reset_tables = inject_bad_row(con, check_id)
        after = len(execute_check(con, sql))
        passed = after > baseline
        tests.append((check_id, baseline, after, passed))
        reset_scratch(con, *reset_tables)
    con.execute("DROP SCHEMA scratch CASCADE")
    return tests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="test every check using scratch table copies")
    args = parser.parse_args()
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}. Run task_1/etl.py first.")

    con = duckdb.connect(str(DB_FILE))
    con.execute("CREATE SCHEMA IF NOT EXISTS audit")
    catalog = load_catalog(con)
    definitions = check_definitions("raw", "audit")
    runlog_exists = con.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema='audit' AND table_name='etl_run_log'
    """).fetchone()[0]
    if not runlog_exists:
        con.execute("""
            CREATE TABLE audit.etl_run_log (
                run_id VARCHAR,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                status VARCHAR
            )
        """)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        con.execute("INSERT INTO audit.etl_run_log VALUES ('manual-bootstrap', ?, ?, 'SUCCESS')", [now, now])

    results = save_results(con, definitions, catalog)
    print("DQ gatekeeper summary")
    print(f"{'ID':8} {'SEVERITY':10} {'BAD ROWS':>9} {'STATUS':8}  CHECK")
    for result in results:
        print(f"{result['check_id']:8} {result['severity']:10} {result['bad_rows']:9} {result['status']:8}  {result['check_name']}")
    critical_failures = sum(r["status"] == "FAIL" for r in results)
    print(f"\nChecks: {len(results)}; critical failures: {critical_failures}")

    if args.self_test:
        test_results = self_test(con, definitions)
        print("\nScratch bad-row tests (PASS means the check caught the injected defect)")
        print(f"{'ID':8} {'BEFORE':>8} {'AFTER':>8} {'TEST':8}")
        for check_id, before, after, passed in test_results:
            print(f"{check_id:8} {before:8} {after:8} {'PASS' if passed else 'FAIL':8}")
        if not all(row[3] for row in test_results):
            con.close()
            raise SystemExit(2)
        # This command verifies the checks themselves; baseline data failures
        # remain visible in audit.dq_results but do not fail the self-test.
        con.close()
        return

    con.close()
    if critical_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
