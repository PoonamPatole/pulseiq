"""Build the department-month cross-source view and PQ-13 reconciliation."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "pulseiq.duckdb"
REFERENCE = ROOT / "data" / "04_Validation_Vault" / "unlock_PQ-13_reference_summary_dept_month.csv"


def main():
    if not DB.exists():
        raise FileNotFoundError("Run the Phase 1 ETL and warehouse build first.")
    if not REFERENCE.exists():
        raise FileNotFoundError(f"PQ-13 reference file not found: {REFERENCE}")

    with duckdb.connect(str(DB)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t13_department_month AS
            WITH months AS (
              SELECT DISTINCT date_trunc('month', period_end_date)::DATE AS month
              FROM warehouse.fact_payroll
            ), departments AS (
              SELECT department_id, department_name FROM warehouse.dim_department
            ), spine AS (
              SELECT d.department_id, d.department_name, m.month
              FROM departments d CROSS JOIN months m
            ), payroll AS (
              SELECT date_trunc('month', period_end_date)::DATE AS month, department_id,
                sum(employer_cost) AS employer_cost,
                sum(gross_pay) AS gross_pay,
                sum(overtime_pay) AS overtime_pay,
                count(DISTINCT employee_id) AS employees_paid,
                sum(overtime_hours_paid) AS overtime_hours
              FROM warehouse.fact_payroll
              -- DQ-02 exact duplicate and DQ-03 orphan rows; preserve in source.
              WHERE payroll_item_id NOT IN ('PI-X0001','PI-X0002','PI-X0003','PI-X0004')
              GROUP BY 1,2
            ), attendance AS (
              SELECT date_trunc('month', period_end_date)::DATE AS month, department_id,
                sum(late_arrivals) AS late_arrivals,
                sum(present_days + 0.5*half_days_unpaid)::DOUBLE /
                  nullif(sum(scheduled_days),0) AS attendance_rate
              FROM warehouse.fact_attendance_monthly
              -- DQ-01 attendance rows recorded after employee exit; preserve in source.
              WHERE attendance_fact_id NOT IN ('FA-X0001','FA-X0002','FA-X0003','FA-X0004')
              GROUP BY 1,2
            ), headcount AS (
              SELECT month_start_date AS month, department_id,
                sum(headcount_end) AS headcount_end,
                sum(hires) AS hires, sum(exits) AS exits,
                100.0*sum(exits)/nullif(sum(headcount_start),0) AS attrition_rate_monthly_pct
              FROM warehouse.fact_headcount_monthly
              GROUP BY 1,2
            ), approved_leave AS (
              SELECT leave_request_id, employee_key, start_date, end_date, days
              FROM warehouse.fact_leave
              WHERE upper(trim(status))='APPROVED'
            ), workdays_by_month AS (
              SELECT l.leave_request_id, d.month_start_date AS month,
                count(*) AS workdays_in_month
              FROM approved_leave l
              CROSS JOIN LATERAL generate_series(l.start_date,l.end_date,INTERVAL 1 DAY) AS gs(day)
              JOIN warehouse.dim_date d ON d.date=gs.day::DATE AND d.is_working_day='Y'
              WHERE l.end_date>=l.start_date
              GROUP BY 1,2
            ), allocated_leave AS (
              SELECT w.month, e.department_id,
                l.days*w.workdays_in_month::DOUBLE /
                  nullif(sum(w.workdays_in_month) OVER (PARTITION BY l.leave_request_id),0) AS leave_days
              FROM workdays_by_month w
              JOIN approved_leave l USING(leave_request_id)
              JOIN warehouse.dim_employee e USING(employee_key)
              UNION ALL
              SELECT date_trunc('month',l.start_date)::DATE AS month,
                e.department_id, l.days::DOUBLE AS leave_days
              FROM approved_leave l
              JOIN warehouse.dim_employee e USING(employee_key)
              WHERE l.end_date<l.start_date OR NOT EXISTS (
                SELECT 1 FROM workdays_by_month w WHERE w.leave_request_id=l.leave_request_id
              )
            ), leave_monthly AS (
              SELECT month, department_id, sum(leave_days) AS approved_leave_days
              FROM allocated_leave GROUP BY 1,2
            ), combined AS (
              SELECT s.department_id, s.department_name, s.month,
                p.employer_cost, p.gross_pay, p.overtime_pay, p.employees_paid,
                p.overtime_hours, a.late_arrivals, a.attendance_rate,
                h.headcount_end, h.hires, h.exits, h.attrition_rate_monthly_pct,
                coalesce(l.approved_leave_days,0) AS approved_leave_days,
                p.employer_cost/nullif(p.employees_paid,0) AS cost_per_head,
                100.0*p.overtime_pay/nullif(p.employer_cost,0) AS overtime_share_pct,
                coalesce(l.approved_leave_days,0)/nullif(h.headcount_end,0) AS leave_days_per_head
              FROM spine s
              LEFT JOIN payroll p USING(department_id,month)
              LEFT JOIN attendance a USING(department_id,month)
              LEFT JOIN headcount h USING(department_id,month)
              LEFT JOIN leave_monthly l USING(department_id,month)
            )
            SELECT * FROM combined ORDER BY month, department_id
        """)
        reference_path = REFERENCE.as_posix().replace("'", "''")
        con.execute(f"""
            CREATE OR REPLACE TABLE metrics.t13_reference AS
            SELECT * FROM read_csv_auto('{reference_path}', header=true)
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t13_reconciliation AS
            WITH joined AS (
              SELECT a.*, r.employer_cost AS ref_employer_cost,
                r.gross_pay AS ref_gross_pay, r.overtime_pay AS ref_overtime_pay,
                r.employees_paid AS ref_employees_paid, r.overtime_hours AS ref_overtime_hours,
                r.late_arrivals AS ref_late_arrivals, r.attendance_rate AS ref_attendance_rate,
                r.headcount_end AS ref_headcount_end, r.hires AS ref_hires,
                r.exits AS ref_exits,
                r.attrition_rate_monthly_pct AS ref_attrition_rate_monthly_pct,
                r.cost_per_head AS ref_cost_per_head,
                r.overtime_share_pct AS ref_overtime_share_pct
              FROM metrics.t13_department_month a
              JOIN metrics.t13_reference r USING(department_id, month)
            ), differences AS (
              SELECT department_id, department_name, month, metric_name, actual_value,
                reference_value, actual_value-reference_value AS difference,
                tolerance,
                CASE WHEN abs(actual_value-reference_value)<=tolerance THEN 'MATCH'
                     ELSE 'DIFFERENCE' END AS result
              FROM joined
              CROSS JOIN LATERAL (VALUES
                ('employer_cost', employer_cost, ref_employer_cost, 0.01),
                ('gross_pay', gross_pay, ref_gross_pay, 0.01),
                ('overtime_pay', overtime_pay, ref_overtime_pay, 0.01),
                ('employees_paid', employees_paid::DOUBLE, ref_employees_paid::DOUBLE, 0.0),
                ('overtime_hours', overtime_hours, ref_overtime_hours, 0.01),
                ('late_arrivals', late_arrivals::DOUBLE, ref_late_arrivals::DOUBLE, 0.0),
                ('attendance_rate', attendance_rate, ref_attendance_rate, 0.000051),
                ('headcount_end', headcount_end::DOUBLE, ref_headcount_end::DOUBLE, 0.0),
                ('hires', hires::DOUBLE, ref_hires::DOUBLE, 0.0),
                ('exits', exits::DOUBLE, ref_exits::DOUBLE, 0.0),
                ('attrition_rate_monthly_pct', attrition_rate_monthly_pct,
                  ref_attrition_rate_monthly_pct, 0.051),
                ('cost_per_head', cost_per_head, ref_cost_per_head, 0.011),
                ('overtime_share_pct', overtime_share_pct, ref_overtime_share_pct, 0.051)
              ) v(metric_name, actual_value, reference_value, tolerance)
            )
            SELECT * FROM differences ORDER BY month, department_id, metric_name
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t13_reconciliation_summary AS
            SELECT result, count(*) AS metric_checks,
              count(DISTINCT department_id || '|' || cast(month AS VARCHAR)) AS department_months
            FROM metrics.t13_reconciliation GROUP BY result ORDER BY result
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t13_leave_quality AS
            SELECT count(*) FILTER (WHERE upper(trim(status))='APPROVED') AS approved_requests,
              count(*) FILTER (WHERE upper(trim(status))='APPROVED' AND end_date<start_date)
                AS invalid_date_ranges,
              coalesce(sum(days) FILTER (WHERE upper(trim(status))='APPROVED' AND end_date<start_date),0)
                AS days_from_invalid_ranges
            FROM warehouse.fact_leave
        """)
    print("Created Task 13 department-month view and PQ-13 reconciliation views.")


if __name__ == "__main__":
    main()
