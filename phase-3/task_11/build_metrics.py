"""Build Task 11 finance aggregates from the Phase 1 warehouse."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "pulseiq.duckdb"


def main():
    if not DB.exists():
        raise FileNotFoundError("Run the Phase 1 ETL and warehouse build first.")
    with duckdb.connect(str(DB)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
        # Group rows are headings: use active detail accounts only.
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t11_pl_monthly AS
            WITH account_lines AS (
              SELECT date_trunc('month', l.entry_date)::DATE AS month,
                     a.account_code, a.account_name, a.account_type,
                     CASE WHEN a.account_type = 'INCOME'
                          THEN -l.signed_amount_debit_positive
                          ELSE l.signed_amount_debit_positive END AS amount
              FROM warehouse.fact_ledger l
              JOIN warehouse.dim_account a USING (account_code)
              WHERE a.statement = 'Profit & Loss'
                AND upper(a.is_group) = 'N' AND upper(a.is_active) = 'Y'
                AND a.account_type IN ('INCOME', 'EXPENSE')
            ), monthly AS (
              SELECT month,
                SUM(amount) FILTER (WHERE account_code BETWEEN 4001 AND 4004) AS revenue,
                SUM(amount) FILTER (WHERE account_code=4900) AS other_income,
                SUM(amount) FILTER (WHERE account_type='EXPENSE') AS expenses
              FROM account_lines GROUP BY month
            )
            SELECT month, revenue, other_income, expenses,
              revenue+coalesce(other_income,0)-expenses AS net_profit,
              100.0*(revenue+coalesce(other_income,0)-expenses)/NULLIF(revenue,0) AS operating_margin_pct
            FROM monthly ORDER BY month
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t11_pl_detail AS
            SELECT date_trunc('month', l.entry_date)::DATE AS month,
              a.account_code, a.account_name, a.account_type,
              CASE WHEN a.account_type='INCOME'
                   THEN -SUM(l.signed_amount_debit_positive)
                   ELSE SUM(l.signed_amount_debit_positive) END AS amount
            FROM warehouse.fact_ledger l
            JOIN warehouse.dim_account a USING(account_code)
            WHERE a.statement='Profit & Loss' AND upper(a.is_group)='N'
              AND upper(a.is_active)='Y' AND a.account_type IN ('INCOME','EXPENSE')
            GROUP BY 1,2,3,4 ORDER BY 1,2
        """)
        # Bills are GST-exclusive and do not represent every ledger expense.
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t11_expense_category AS
            SELECT date_trunc('month', e.expense_date)::DATE AS month,
              e.category_account AS account_code, a.account_name AS category,
              SUM(e.amount_excl_gst) AS expense_amount
            FROM warehouse.fact_expense e
            LEFT JOIN warehouse.dim_account a ON a.account_code=e.category_account
            GROUP BY 1,2,3 ORDER BY 1,4 DESC
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t11_vendor_spend AS
            SELECT date_trunc('month', e.expense_date)::DATE AS month,
              e.vendor_id, v.vendor_name, SUM(e.amount_excl_gst) AS expense_amount
            FROM warehouse.fact_expense e
            LEFT JOIN warehouse.dim_vendor v USING(vendor_id)
            GROUP BY 1,2,3 ORDER BY 1,4 DESC
        """)
        con.execute("""
            CREATE OR REPLACE VIEW metrics.t11_tieout AS
            WITH governed AS (
              SELECT month_start_date AS month, SUM(metric_value) AS revenue
              FROM metrics.m16_revenue GROUP BY 1
            ), profit AS (
              SELECT month_start_date AS month, metric_value AS net_profit
              FROM metrics.m17_net_profit
            ), margin AS (
              SELECT month_start_date AS month, metric_value AS margin_pct
              FROM metrics.m18_operating_margin
            )
            SELECT p.month, p.revenue AS task_revenue,
              g.revenue AS governed_revenue, p.revenue-g.revenue AS revenue_difference,
              p.net_profit AS task_net_profit, n.net_profit AS governed_net_profit,
              p.net_profit-n.net_profit AS profit_difference,
              p.operating_margin_pct AS task_margin_pct, m.margin_pct AS governed_margin_pct,
              p.operating_margin_pct-m.margin_pct AS margin_difference_pp
            FROM metrics.t11_pl_monthly p
            LEFT JOIN governed g USING(month)
            LEFT JOIN profit n USING(month)
            LEFT JOIN margin m USING(month)
            ORDER BY p.month
        """)
    print("Created Task 11 P&L, expense, vendor, and tie-out views in metrics schema.")


if __name__ == "__main__":
    main()
