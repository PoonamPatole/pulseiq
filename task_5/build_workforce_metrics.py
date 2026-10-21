"""Create dashboard-safe workforce metric views for Task 5.

The Streamlit app reads only views in the metrics schema. This setup script
builds the department/location/work-mode aggregates from Task 2's warehouse.
"""

from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"


def main() -> None:
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database missing: {DB_FILE}. Run Tasks 1 and 2 first.")
    con = duckdb.connect(str(DB_FILE))
    con.execute("CREATE SCHEMA IF NOT EXISTS metrics")

    # A company total is a safe aggregate (the group is much larger than five)
    # and avoids summing department buckets that are suppressed for privacy.
    con.execute("""
        CREATE OR REPLACE VIEW metrics.m01_company_headcount AS
        SELECT month_start_date,
               SUM(headcount_end)::DOUBLE AS metric_value
        FROM warehouse.fact_headcount_monthly
        GROUP BY month_start_date
        HAVING SUM(headcount_end) >= 5
    """)

    con.execute("""
        CREATE OR REPLACE VIEW metrics.m01_department_headcount AS
        SELECT h.month_start_date, h.department_id, d.department_name,
               h.metric_value
        FROM metrics.m01_headcount h
        LEFT JOIN warehouse.dim_department d USING (department_id)
    """)

    con.execute("""
        CREATE OR REPLACE VIEW metrics.m29_headcount_growth_mom AS
        WITH monthly AS (
            SELECT month_start_date, 'Company' AS scope,
                   NULL::VARCHAR AS department_id, metric_value AS headcount
            FROM metrics.m01_company_headcount
            UNION ALL
            SELECT month_start_date, 'Department' AS scope,
                   department_id, metric_value AS headcount
            FROM metrics.m01_department_headcount
        ), lagged AS (
            SELECT month_start_date, scope, department_id, headcount,
                   LAG(headcount) OVER (
                       PARTITION BY scope, department_id ORDER BY month_start_date
                   ) AS previous_headcount
            FROM monthly
        )
        SELECT month_start_date, scope, department_id, headcount,
               previous_headcount,
               100.0 * (headcount - previous_headcount) /
                   NULLIF(previous_headcount, 0) AS metric_value
        FROM lagged
        WHERE previous_headcount IS NOT NULL AND headcount >= 5
    """)

    # Extend the 28 source-dictionary rows with the documented project metric.
    # A base snapshot prevents repeated Task 5 builds from duplicating M29.
    con.execute("""
        CREATE OR REPLACE TABLE metrics.metric_catalog_base AS
        SELECT * FROM metrics.metric_catalog WHERE metric_id <> 'M29'
    """)
    con.execute("""
        CREATE OR REPLACE VIEW metrics.metric_catalog AS
        SELECT * FROM metrics.metric_catalog_base
        UNION ALL
        SELECT 'M29'::VARCHAR AS metric_id,
               'Headcount growth (month over month)'::VARCHAR AS metric_name,
               'Percentage change in period-end headcount from the previous month.'::VARCHAR AS business_definition,
               'metrics.m01_company_headcount / metrics.m01_department_headcount'::VARCHAR AS source_table,
               'Company or department x month'::VARCHAR AS grain,
               'Month over month'::VARCHAR AS time_period,
               'People Analytics'::VARCHAR AS owner_team,
               'percent'::VARCHAR AS unit,
               'Higher is better when workforce growth is planned'::VARCHAR AS good_direction,
               'First month has no prior month; groups below five are suppressed.'::VARCHAR AS caveat,
               NULL::BIGINT AS dictionary_minimum_group_size,
               5::BIGINT AS minimum_group_size
    """)

    employee_month = """
        WITH months AS (
            SELECT DISTINCT month_start_date,
                   last_day(month_start_date) AS month_end_date
            FROM warehouse.fact_headcount_monthly
        ), versions AS (
            SELECT m.month_start_date, e.employee_id, e.department_id,
                   e.work_location, e.work_mode, e.valid_from, e.employee_key,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.month_start_date, e.employee_id
                       ORDER BY e.valid_from DESC, e.employee_key DESC
                   ) AS version_rank
            FROM months m
            JOIN warehouse.dim_employee e
              ON e.valid_from <= m.month_end_date
             AND COALESCE(e.valid_to, DATE '9999-12-31') >= m.month_end_date
             AND e.hire_date <= m.month_end_date
             AND (e.exit_date IS NULL OR e.exit_date > m.month_end_date)
        )
        SELECT month_start_date, employee_id, department_id,
               COALESCE(work_location, 'Unknown') AS work_location,
               COALESCE(work_mode, 'Unknown') AS work_mode
        FROM versions
        WHERE version_rank = 1
    """

    con.execute(f"""
        CREATE OR REPLACE VIEW metrics.m01_headcount_by_location_tier AS
        WITH employee_month AS ({employee_month})
        SELECT e.month_start_date, e.department_id,
               COALESCE(l.city_tier, 'Unknown') AS category,
               COUNT(DISTINCT e.employee_id)::DOUBLE AS metric_value,
               COUNT(DISTINCT e.employee_id)::BIGINT AS group_size
        FROM employee_month e
        LEFT JOIN warehouse.dim_location l USING (work_location)
        GROUP BY 1, 2, 3
        HAVING COUNT(DISTINCT e.employee_id) >= 5
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW metrics.m01_headcount_by_work_mode AS
        WITH employee_month AS ({employee_month})
        SELECT month_start_date, department_id, work_mode AS category,
               COUNT(DISTINCT employee_id)::DOUBLE AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM employee_month
        GROUP BY 1, 2, 3
        HAVING COUNT(DISTINCT employee_id) >= 5
    """)

    print("Created dashboard metric views:")
    for name in (
        "m01_company_headcount",
        "m01_department_headcount",
        "m29_headcount_growth_mom",
        "m01_headcount_by_location_tier",
        "m01_headcount_by_work_mode",
    ):
        rows = con.execute(f"SELECT COUNT(*) FROM metrics.{name}").fetchone()[0]
        print(f"metrics.{name}: {rows} visible rows")

    print("Location and work-mode charts suppress small department/category groups;")
    print("their visible category totals can be lower than company headcount.")
    con.close()


if __name__ == "__main__":
    main()
