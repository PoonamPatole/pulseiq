"""Build the eight-KPI executive scorecard from governed metric views."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"


def main():
    if not DB.exists():
        raise FileNotFoundError("Run the project warehouse and metric-view builders first.")
    with duckdb.connect(str(DB)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t15_scorecard AS
            WITH months AS (
              SELECT DISTINCT month FROM warehouse.kpi_targets
            ), metric_values AS (
              SELECT month_start_date AS month, 'M01' AS metric_id,
                metric_value, NULL::DOUBLE AS target_value,
                'metrics.m01_company_headcount' AS source_view
              FROM metrics.m01_company_headcount
              UNION ALL
              SELECT month_start_date, 'M16', sum(metric_value), NULL::DOUBLE,
                'metrics.m16_revenue'
              FROM metrics.m16_revenue GROUP BY 1
              UNION ALL
              SELECT month_start_date, 'M17', metric_value, NULL::DOUBLE,
                'metrics.m17_net_profit'
              FROM metrics.m17_net_profit
              UNION ALL
              SELECT month_start_date, 'M18', metric_value, NULL::DOUBLE,
                'metrics.m18_operating_margin'
              FROM metrics.m18_operating_margin
              UNION ALL
              SELECT a.month_start_date, 'M04', avg(a.metric_value),
                avg(k.attrition_monthly_target_pct)::DOUBLE,
                'metrics.m04_attrition_rate_monthly + warehouse.kpi_targets'
              FROM metrics.m04_attrition_rate_monthly a
              JOIN warehouse.kpi_targets k
                ON k.month=a.month_start_date AND k.department_id=a.department_id
              GROUP BY 1
              UNION ALL
              SELECT date_trunc('month',a.month_end_date)::DATE, 'M13', 100.0*avg(a.metric_value),
                100.0*avg(k.attendance_rate_target)::DOUBLE,
                'metrics.m13_attendance_rate + warehouse.kpi_targets'
              FROM metrics.m13_attendance_rate a
              JOIN warehouse.kpi_targets k
                ON k.month=date_trunc('month',a.month_end_date)::DATE
                AND k.department_id=a.department_id
              GROUP BY 1
              UNION ALL
              SELECT date_trunc('month',o.month_end_date)::DATE, 'M11',
                sum(o.metric_value*p.metric_value)/nullif(sum(p.metric_value),0),
                sum(k.overtime_share_target_pct*p.metric_value)/nullif(sum(p.metric_value),0),
                'metrics.m11_overtime_share + metrics.m09_employer_payroll_cost + warehouse.kpi_targets'
              FROM metrics.m11_overtime_share o
              JOIN metrics.m09_employer_payroll_cost p
                ON p.month_end_date=o.month_end_date AND p.department_id=o.department_id
              JOIN warehouse.kpi_targets k
                ON k.month=date_trunc('month',o.month_end_date)::DATE
                AND k.department_id=o.department_id
              GROUP BY 1
              UNION ALL
              SELECT month, 'M22', avg(task_completion_pct),
                avg(task_completion_target_pct)::DOUBLE,
                'metrics.t10_kpi_scorecard'
              FROM metrics.t10_kpi_scorecard
              WHERE task_completion_pct IS NOT NULL
              GROUP BY 1
            ), scorecard AS (
              SELECT v.month, v.metric_id, d.metric_name, d.formula,
                d.source_table, d.grain, d.unit, d.good_direction,
                v.metric_value, v.target_value, v.source_view,
                lag(v.metric_value) OVER (PARTITION BY v.metric_id ORDER BY v.month) AS prior_value
              FROM metric_values v
              JOIN months m USING(month)
              JOIN raw.metric_dictionary d USING(metric_id)
            )
            SELECT *, metric_value-prior_value AS month_delta,
              100.0*(metric_value-prior_value)/nullif(abs(prior_value),0) AS month_change_pct,
              CASE
                WHEN metric_value IS NULL THEN 'NO DATA'
                WHEN target_value IS NULL THEN 'NO TARGET'
                WHEN metric_id IN ('M04','M11') AND metric_value<=target_value THEN 'ON TARGET'
                WHEN metric_id IN ('M13','M22') AND metric_value>=target_value THEN 'ON TARGET'
                WHEN metric_id IN ('M04','M11','M13','M22') THEN 'NEEDS ATTENTION'
                ELSE 'NO TARGET'
              END AS status
            FROM scorecard
            ORDER BY month, metric_id
        """)
    print("Created metrics.t15_scorecard with governed values, targets, month trends, and status.")


if __name__ == "__main__":
    main()
