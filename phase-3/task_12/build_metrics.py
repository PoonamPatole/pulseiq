"""Build Task 12 receivables and cash flow views."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "pulseiq.duckdb"


def main():
    if not DB.exists():
        raise FileNotFoundError("Run the Phase 1 ETL and warehouse build first.")
    with duckdb.connect(str(DB)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t12_open_receivables AS
            WITH open_rows AS (
              SELECT i.invoice_id, i.invoice_number, i.client_id,
                c.client_name, c.payment_terms_days, i.invoice_date, i.due_date,
                upper(trim(i.status)) AS status, i.balance_due,
                greatest(coalesce(i.days_past_due_at_cutoff, 0), 0) AS days_past_due
              FROM warehouse.fact_invoice i
              LEFT JOIN warehouse.dim_client c USING(client_id)
              WHERE upper(trim(i.status)) IN ('SENT','OVERDUE','PARTIALLY_PAID')
                AND coalesce(i.balance_due, 0) > 0
            )
            SELECT *, CASE
              WHEN days_past_due <= 30 THEN '0-30 days'
              WHEN days_past_due <= 60 THEN '31-60 days'
              WHEN days_past_due <= 90 THEN '61-90 days'
              ELSE '90+ days' END AS ageing_bucket
            FROM open_rows
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t12_ar_buckets AS
            WITH bucket_names(ageing_bucket, sort_order) AS (
              VALUES ('0-30 days',1),('31-60 days',2),('61-90 days',3),('90+ days',4)
            ), totals AS (
              SELECT ageing_bucket, sum(balance_due) AS receivables,
                count(*) AS invoice_count
              FROM metrics.t12_open_receivables GROUP BY 1
            )
            SELECT b.ageing_bucket, coalesce(t.receivables,0) AS receivables,
              coalesce(t.invoice_count,0) AS invoice_count, b.sort_order
            FROM bucket_names b LEFT JOIN totals t USING(ageing_bucket)
            ORDER BY b.sort_order
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t12_bucket_check AS
            SELECT coalesce(sum(balance_due),0) AS open_receivables,
              coalesce((SELECT sum(receivables) FROM metrics.t12_ar_buckets),0) AS bucket_total,
              coalesce(sum(balance_due),0)-coalesce(
                (SELECT sum(receivables) FROM metrics.t12_ar_buckets),0) AS difference,
              count(*) AS open_invoice_count
            FROM metrics.t12_open_receivables
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t12_client_days_to_pay AS
            SELECT i.client_id, c.client_name, c.payment_terms_days,
              count(*) AS paid_invoice_count,
              avg(i.days_to_pay) AS average_days_to_pay,
              max(i.days_to_pay) AS maximum_days_to_pay
            FROM warehouse.fact_invoice i
            JOIN warehouse.dim_client c USING(client_id)
            WHERE upper(trim(i.status))='PAID' AND i.days_to_pay IS NOT NULL
            GROUP BY 1,2,3
            ORDER BY average_days_to_pay DESC
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t12_overdue_clients AS
            SELECT client_id, client_name, payment_terms_days,
              count(*) AS overdue_invoice_count,
              sum(balance_due) AS overdue_balance,
              max(days_past_due) AS oldest_days_past_due
            FROM metrics.t12_open_receivables
            WHERE days_past_due > 0
            GROUP BY 1,2,3
            ORDER BY overdue_balance DESC
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t12_cash_monthly AS
            WITH cash_in AS (
              SELECT date_trunc('month', payment_date)::DATE AS month,
                sum(amount) AS cash_received
              FROM warehouse.fact_invoice_payment
              WHERE payment_date IS NOT NULL
              GROUP BY 1
            ), cash_out AS (
              SELECT date_trunc('month', paid_date)::DATE AS month,
                sum(total_amount) AS cash_paid
              FROM warehouse.fact_expense
              WHERE paid_date IS NOT NULL
              GROUP BY 1
            )
            SELECT coalesce(i.month,o.month) AS month,
              coalesce(i.cash_received,0) AS cash_in,
              coalesce(o.cash_paid,0) AS cash_out,
              coalesce(i.cash_received,0)-coalesce(o.cash_paid,0) AS net_cash_flow
            FROM cash_in i FULL OUTER JOIN cash_out o USING(month)
            ORDER BY month
        """)
    print("Created Task 12 receivables ageing, client payment, overdue, cash, and bucket-check views.")


if __name__ == "__main__":
    main()
