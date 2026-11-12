"""Build Task 14 anomaly and forecast views."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"


def main():
    if not DB.exists():
        raise FileNotFoundError("Run the Phase 1 ETL and warehouse build first.")
    with duckdb.connect(str(DB)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t14_anomalies_by_type AS
            SELECT source_dataset, reason_code,
              CASE reason_code
                WHEN 'STATISTICAL_OUTLIER' THEN 'Unusual pay ratios'
                WHEN 'GROSS_ABOVE_NORM' THEN 'Gross pay unusually high'
                WHEN 'GROSS_BELOW_EXPECTED' THEN 'Gross pay below expected'
                WHEN 'NEGATIVE_NET_PAY' THEN 'Deductions exceed gross pay'
                WHEN 'ZERO_PAY' THEN 'Zero pay for active employee'
                WHEN 'OVERTIME_ABOVE_CAP' THEN 'Overtime above cap'
                WHEN 'PF_NOT_DEDUCTED' THEN 'Missing employer PF'
                WHEN 'NO_ATTENDANCE' THEN 'No attendance recorded'
                WHEN 'FREQUENT_LATE' THEN 'Frequent late arrivals'
                WHEN 'PATTERN_SHIFT' THEN 'Attendance pattern changed'
                WHEN 'LONG_UNPAID_ABSENCE' THEN 'Long unpaid absence'
                ELSE reason_code END AS reason_label,
              count(*) AS anomaly_count,
              count(money_at_risk) AS quantified_count,
              sum(money_at_risk) AS money_at_risk,
              max(anomaly_score) AS highest_anomaly_score
            FROM warehouse.fact_anomaly
            WHERE upper(trim(flagged))='Y'
            GROUP BY source_dataset, reason_code
            ORDER BY money_at_risk DESC NULLS LAST, source_dataset, reason_code
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t14_actuals AS
            SELECT 'headcount_end' AS metric, month_start_date AS month,
              sum(headcount_end)::DOUBLE AS actual_value
            FROM warehouse.fact_headcount_monthly
            GROUP BY month_start_date
            UNION ALL
            SELECT 'attrition_rate_monthly_pct', month_start_date,
              100.0*sum(exits)/nullif(sum(headcount_start),0)
            FROM warehouse.fact_headcount_monthly
            GROUP BY month_start_date
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t14_forecast_accuracy AS
            SELECT f.forecast_id, f.metric, f.forecast_month AS month,
              f.forecast_value, f.lower_80, f.upper_80, f.method,
              f.trained_through, f.model_version,
              a.actual_value,
              abs(f.forecast_value-a.actual_value) AS absolute_error,
              100.0*abs(f.forecast_value-a.actual_value)/nullif(abs(a.actual_value),0)
                AS absolute_percentage_error,
              CASE WHEN a.actual_value IS NULL THEN 'NO ACTUAL YET'
                   ELSE 'ACTUAL AVAILABLE' END AS actual_status
            FROM warehouse.fact_forecast f
            LEFT JOIN metrics.t14_actuals a
              ON a.metric=f.metric AND a.month=f.forecast_month
            WHERE f.department_id='ALL'
            ORDER BY f.metric, f.forecast_month
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t14_forecast_error_summary AS
            SELECT metric, count(*) AS forecast_months,
              count(actual_value) AS months_with_actuals,
              avg(absolute_percentage_error) AS mape_pct
            FROM metrics.t14_forecast_accuracy
            GROUP BY metric ORDER BY metric
        """)
    print("Created Task 14 anomaly, actual, forecast accuracy, and error summary views.")


if __name__ == "__main__":
    main()
