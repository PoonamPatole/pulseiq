"""Build the reusable PulseIQ metric layer in the DuckDB metrics schema."""

from __future__ import annotations

from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"

# Metrics use warehouse tables created in Task 2. The dictionary supplies their
# official names, descriptions, owners, units, and privacy thresholds.
VIEWS = {
    "M01": ("headcount", """
        SELECT month_start_date, department_id,
               headcount_end::DOUBLE AS metric_value,
               headcount_end::BIGINT AS group_size
        FROM warehouse.fact_headcount_monthly
    """),
    "M02": ("hires", """
        SELECT month_start_date, department_id, SUM(hires)::DOUBLE AS metric_value,
               SUM(hires)::BIGINT AS group_size
        FROM warehouse.fact_headcount_monthly GROUP BY 1, 2
    """),
    "M03": ("exits", """
        SELECT month_start_date, department_id, SUM(exits)::DOUBLE AS metric_value,
               SUM(headcount_start)::BIGINT AS group_size
        FROM warehouse.fact_headcount_monthly GROUP BY 1, 2
    """),
    "M04": ("attrition_rate_monthly", """
        SELECT month_start_date, department_id,
               100.0 * SUM(exits) / NULLIF(SUM(headcount_start), 0) AS metric_value,
               SUM(headcount_start)::BIGINT AS group_size
        FROM warehouse.fact_headcount_monthly GROUP BY 1, 2
    """),
    "M05": ("attrition_rate_rolling_12m", """
        WITH monthly AS (
            SELECT month_start_date, department_id, SUM(exits) AS exits,
                   SUM(headcount_end) AS headcount_end
            FROM warehouse.fact_headcount_monthly GROUP BY 1, 2
        ), rolling AS (
            SELECT *, SUM(exits) OVER w AS exits_12m,
                   AVG(headcount_end) OVER w AS avg_headcount_12m,
                   COUNT(*) OVER w AS months_in_window
            FROM monthly WINDOW w AS (
                PARTITION BY department_id ORDER BY month_start_date
                ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
        )
        SELECT month_start_date, department_id,
               100.0 * exits_12m / NULLIF(avg_headcount_12m, 0) AS metric_value,
               headcount_end::BIGINT AS group_size
        FROM rolling WHERE months_in_window = 12
    """),
    "M06": ("voluntary_attrition_rate", """
        WITH monthly AS (
            SELECT month_start_date, department_id, SUM(voluntary_exits) AS exits,
                   SUM(headcount_end) AS headcount_end
            FROM warehouse.fact_headcount_monthly GROUP BY 1, 2
        ), rolling AS (
            SELECT *, SUM(exits) OVER w AS exits_12m,
                   AVG(headcount_end) OVER w AS avg_headcount_12m,
                   COUNT(*) OVER w AS months_in_window
            FROM monthly WINDOW w AS (
                PARTITION BY department_id ORDER BY month_start_date
                ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
        )
        SELECT month_start_date, department_id,
               100.0 * exits_12m / NULLIF(avg_headcount_12m, 0) AS metric_value,
               headcount_end::BIGINT AS group_size
        FROM rolling WHERE months_in_window = 12
    """),
    # Employee-level pay is intentionally aggregated to department-month to
    # prevent a view from disclosing a named person's salary.
    "M07": ("gross_pay", """
        SELECT period_end_date AS month_end_date, department_id,
               SUM(gross_pay)::DOUBLE AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M08": ("net_pay", """
        SELECT period_end_date AS month_end_date, department_id,
               SUM(net_pay)::DOUBLE AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M09": ("employer_payroll_cost", """
        SELECT period_end_date AS month_end_date, department_id,
               SUM(employer_cost)::DOUBLE AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M10": ("cost_per_head", """
        SELECT period_end_date AS month_end_date, department_id,
               SUM(employer_cost) / NULLIF(COUNT(DISTINCT employee_id), 0)::DOUBLE AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M11": ("overtime_share", """
        SELECT period_end_date AS month_end_date, department_id,
               100.0 * SUM(overtime_pay) / NULLIF(SUM(employer_cost), 0) AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M12": ("variable_pay_share", """
        SELECT period_end_date AS month_end_date, department_id,
               100.0 * SUM(variable_pay) / NULLIF(SUM(gross_pay), 0) AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M13": ("attendance_rate", """
        SELECT period_end_date AS month_end_date, department_id,
               (SUM(present_days) + 0.5 * SUM(half_days_unpaid)) /
                   NULLIF(SUM(scheduled_days), 0) AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_attendance_monthly GROUP BY 1, 2
    """),
    "M14": ("late_arrival_rate", """
        SELECT period_end_date AS month_end_date, department_id,
               SUM(late_arrivals)::DOUBLE / NULLIF(SUM(present_days), 0) AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_attendance_monthly GROUP BY 1, 2
    """),
    "M15": ("leave_without_pay_days", """
        SELECT period_end_date AS month_end_date, department_id,
               SUM(lop_days)::DOUBLE AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_payroll GROUP BY 1, 2
    """),
    "M16": ("revenue", """
        SELECT d.month_start_date, l.account_code,
               -SUM(l.signed_amount_debit_positive)::DOUBLE AS metric_value,
               COUNT(*)::BIGINT AS group_size
        FROM warehouse.fact_ledger l
        JOIN warehouse.dim_date d ON d.date_key = l.date_key
        WHERE l.account_code BETWEEN 4001 AND 4004
        GROUP BY 1, 2
    """),
    "M17": ("net_profit", """
        SELECT d.month_start_date,
               -SUM(l.signed_amount_debit_positive)::DOUBLE AS metric_value,
               COUNT(*)::BIGINT AS group_size
        FROM warehouse.fact_ledger l
        JOIN warehouse.dim_date d ON d.date_key = l.date_key
        WHERE (l.account_code BETWEEN 4000 AND 4999)
           OR (l.account_code BETWEEN 5000 AND 5999)
        GROUP BY 1
    """),
    "M18": ("operating_margin", """
        WITH monthly AS (
            SELECT d.month_start_date,
                   -SUM(CASE WHEN l.account_code BETWEEN 4001 AND 4004
                             THEN l.signed_amount_debit_positive ELSE 0 END) AS revenue,
                   -SUM(CASE WHEN l.account_code BETWEEN 4000 AND 4999
                                  OR l.account_code BETWEEN 5000 AND 5999
                             THEN l.signed_amount_debit_positive ELSE 0 END) AS net_profit,
                   COUNT(*) AS group_size
            FROM warehouse.fact_ledger l
            JOIN warehouse.dim_date d ON d.date_key = l.date_key
            GROUP BY 1
        )
        SELECT month_start_date,
               100.0 * net_profit / NULLIF(revenue, 0) AS metric_value,
               group_size::BIGINT AS group_size FROM monthly
    """),
    "M19": ("payroll_as_percent_of_revenue", """
        WITH ledger_monthly AS (
            SELECT d.month_start_date,
                   SUM(CASE WHEN l.account_code BETWEEN 5001 AND 5005
                            THEN l.signed_amount_debit_positive ELSE 0 END) AS payroll_cost,
                   -SUM(CASE WHEN l.account_code BETWEEN 4001 AND 4004
                             THEN l.signed_amount_debit_positive ELSE 0 END) AS revenue,
                   COUNT(*) AS ledger_lines
            FROM warehouse.fact_ledger l
            JOIN warehouse.dim_date d ON d.date_key = l.date_key
            GROUP BY 1
        ), payroll_population AS (
            SELECT date_trunc('month', period_end_date)::DATE AS month_start_date,
                   COUNT(DISTINCT employee_id) AS group_size
            FROM warehouse.fact_payroll GROUP BY 1
        ), monthly AS (
            SELECT l.*, COALESCE(p.group_size, 0) AS group_size
            FROM ledger_monthly l
            LEFT JOIN payroll_population p USING (month_start_date)
        )
        SELECT month_start_date,
               100.0 * payroll_cost / NULLIF(revenue, 0) AS metric_value,
               group_size::BIGINT AS group_size FROM monthly
    """),
    # Invoice balances are a snapshot at the dataset cutoff, not historical
    # month-end balances. We publish the point-in-time 30-Sep-2026 DSO only.
    "M20": ("days_sales_outstanding", """
        WITH cutoff AS (SELECT DATE '2026-09-30' AS report_date),
        values_at_cutoff AS (
            SELECT c.report_date,
                   SUM(i.balance_due) AS receivables,
                   SUM(i.total_amount) FILTER (
                       WHERE i.invoice_date > c.report_date - INTERVAL 90 DAY
                         AND i.invoice_date <= c.report_date) AS credit_sales_90d,
                   COUNT(DISTINCT i.invoice_id) AS group_size
            FROM warehouse.fact_invoice i CROSS JOIN cutoff c
            GROUP BY c.report_date
        )
        SELECT report_date,
               receivables / NULLIF(credit_sales_90d, 0) * 90 AS metric_value,
               group_size::BIGINT AS group_size FROM values_at_cutoff
    """),
    "M21": ("overdue_receivables", """
        SELECT DATE '2026-09-30' AS report_date, client_id,
               SUM(balance_due)::DOUBLE AS metric_value,
               COUNT(DISTINCT invoice_id)::BIGINT AS group_size
        FROM warehouse.fact_invoice
        WHERE due_date < DATE '2026-09-30'
          AND UPPER(status) NOT IN ('DRAFT', 'CANCELLED')
        GROUP BY client_id
    """),
    "M22": ("task_completion_rate", """
        SELECT t.team_id, t.sprint_id,
               COUNT(*) FILTER (WHERE UPPER(t.status) = 'DONE')::DOUBLE /
                   NULLIF(COUNT(*) FILTER (WHERE UPPER(t.status) <> 'CANCELLED'), 0) AS metric_value,
               COUNT(*) FILTER (WHERE UPPER(t.status) <> 'CANCELLED')::BIGINT AS group_size
        FROM warehouse.fact_task t GROUP BY 1, 2
    """),
    "M23": ("on_time_delivery_rate", """
        SELECT team_id, sprint_id,
               COUNT(*) FILTER (WHERE UPPER(status) = 'DONE' AND UPPER(completed_on_time) = 'Y')::DOUBLE /
                   NULLIF(COUNT(*) FILTER (WHERE UPPER(status) = 'DONE'), 0) AS metric_value,
               COUNT(*) FILTER (WHERE UPPER(status) = 'DONE')::BIGINT AS group_size
        FROM warehouse.fact_task GROUP BY 1, 2
    """),
    "M24": ("velocity", """
        SELECT team_id, sprint_id,
               SUM(story_points) FILTER (WHERE UPPER(status) = 'DONE')::DOUBLE AS metric_value,
               COUNT(*) FILTER (WHERE UPPER(status) = 'DONE')::BIGINT AS group_size
        FROM warehouse.fact_task GROUP BY 1, 2
    """),
    "M25": ("average_cycle_time", """
        SELECT team_id, sprint_id,
               AVG(cycle_time_days) FILTER (
                   WHERE UPPER(status) = 'DONE' AND cycle_time_days >= 0) AS metric_value,
               COUNT(*) FILTER (
                   WHERE UPPER(status) = 'DONE' AND cycle_time_days >= 0)::BIGINT AS group_size
        FROM warehouse.fact_task GROUP BY 1, 2
    """),
    "M26": ("anomaly_flag_rate", """
        SELECT source_dataset, date_trunc('month', period)::DATE AS month_start_date,
               COUNT(*) FILTER (WHERE UPPER(flagged) = 'Y')::DOUBLE /
                   NULLIF(COUNT(*), 0) AS metric_value,
               COUNT(*)::BIGINT AS group_size
        FROM warehouse.fact_anomaly GROUP BY 1, 2
    """),
    # Employee IDs are never selected; only department-level aggregates leave
    # the metric layer. The group size uses distinct employees, not rows.
    "M27": ("high_risk_share", """
        SELECT department_id,
               COUNT(DISTINCT employee_id) FILTER (WHERE UPPER(risk_band) = 'HIGH')::DOUBLE /
                   NULLIF(COUNT(DISTINCT employee_id), 0) AS metric_value,
               COUNT(DISTINCT employee_id)::BIGINT AS group_size
        FROM warehouse.fact_attrition_risk GROUP BY department_id
    """),
    "M28": ("forecast_error_mape", """
        WITH actuals AS (
            SELECT month_start_date, SUM(headcount_end) AS actual_value
            FROM warehouse.fact_headcount_monthly GROUP BY month_start_date
        )
        SELECT f.forecast_month AS month_start_date, f.department_id,
               AVG(ABS(a.actual_value - f.forecast_value) /
                   NULLIF(a.actual_value, 0)) * 100 AS metric_value,
               COUNT(*)::BIGINT AS group_size,
               CASE WHEN COUNT(a.actual_value) = 0 THEN 'NO_ACTUALS_YET' ELSE 'CALCULATED' END AS data_status
        FROM warehouse.fact_forecast f
        LEFT JOIN actuals a ON a.month_start_date = f.forecast_month
        WHERE LOWER(f.metric) = 'headcount_end'
        GROUP BY 1, 2
    """),
}


def main() -> None:
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database missing: {DB_FILE}. Run Task 1 and Task 2 first.")
    con = duckdb.connect(str(DB_FILE))
    con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
    dictionary_count = con.execute("SELECT COUNT(*) FROM raw.metric_dictionary").fetchone()[0]
    if dictionary_count != 28:
        raise ValueError(f"Expected 28 dictionary rows; found {dictionary_count}.")

    con.execute("""
        CREATE OR REPLACE VIEW metrics.metric_catalog AS
        SELECT metric_id, metric_name, business_definition, source_table, grain,
               time_period, owner_team, unit, good_direction, caveat,
               TRY_CAST(REGEXP_EXTRACT(minimum_group_size, '[0-9]+', 0) AS BIGINT)
                   AS dictionary_minimum_group_size,
               CASE metric_id
                   WHEN 'M19' THEN 5  -- payroll population for company-level payroll share
                   WHEN 'M24' THEN 5  -- do not display velocity for fewer than 5 completed tasks
                   WHEN 'M26' THEN 10 -- suppress small AI scoring groups
                   ELSE COALESCE(
                       TRY_CAST(REGEXP_EXTRACT(minimum_group_size, '[0-9]+', 0) AS BIGINT), 1)
               END AS minimum_group_size
        FROM raw.metric_dictionary
    """)

    for metric_id, (slug, query) in VIEWS.items():
        catalog_id = metric_id
        # The outer filter applies the dictionary's privacy threshold uniformly.
        view_name = f"{metric_id.lower()}_{slug}"
        con.execute(f"""
            CREATE OR REPLACE VIEW metrics.{view_name} AS
            SELECT q.* EXCLUDE (group_size)
            FROM ({query}) q
            JOIN metrics.metric_catalog c ON c.metric_id = '{catalog_id}'
            WHERE q.group_size >= c.minimum_group_size
        """)

    if len(VIEWS) != 28:
        raise AssertionError(f"Implementation has {len(VIEWS)} views, expected 28")

    print("Metric catalog:")
    print(con.execute("SELECT metric_id, metric_name, minimum_group_size FROM metrics.metric_catalog ORDER BY metric_id").df().to_string(index=False))
    print("\nView inventory:")
    inventory = con.execute("""
        SELECT table_name AS view_name
        FROM information_schema.views
        WHERE table_schema = 'metrics' AND table_name <> 'metric_catalog'
        ORDER BY table_name
    """).fetchall()
    print(f"{len(inventory)} metric views created.")
    for (view_name,) in inventory:
        n = con.execute(f"SELECT COUNT(*) FROM metrics.{view_name}").fetchone()[0]
        print(f"{view_name}: {n} visible rows")
    print("\nForecast error note: NO_ACTUALS_YET rows have NULL metric_value until actuals arrive.")
    con.close()


if __name__ == "__main__":
    main()
