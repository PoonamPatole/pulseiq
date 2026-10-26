"""Load budget and targets into the warehouse and build Task 10 aggregates."""
from pathlib import Path
import duckdb

ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"pulseiq.duckdb"

def main():
    if not DB.exists(): raise FileNotFoundError("Run the project ETL and warehouse builder first.")
    with duckdb.connect(str(DB)) as c:
        c.execute("CREATE SCHEMA IF NOT EXISTS warehouse")
        c.execute("CREATE OR REPLACE TABLE warehouse.budget_payroll_dept_month AS SELECT department_id,month,budget_payroll_cost FROM raw.budget_payroll_dept_month")
        c.execute("CREATE OR REPLACE TABLE warehouse.kpi_targets AS SELECT * FROM raw.kpi_targets")
        c.execute("CREATE SCHEMA IF NOT EXISTS metrics")
        c.execute("""CREATE OR REPLACE VIEW metrics.t10_budget_variance AS
          WITH actual AS (
            SELECT date_trunc('month',period_end_date)::DATE AS month,department_id,
              SUM(employer_cost) AS actual_cost,COUNT(DISTINCT employee_id) AS employee_count
            FROM warehouse.fact_payroll GROUP BY 1,2 HAVING COUNT(DISTINCT employee_id)>=5
          )
          SELECT a.month,a.department_id,d.department_name,a.actual_cost,b.budget_payroll_cost AS budget,
            a.actual_cost-b.budget_payroll_cost AS variance,
            100.0*(a.actual_cost-b.budget_payroll_cost)/NULLIF(b.budget_payroll_cost,0) AS variance_pct,
            a.employee_count,a.actual_cost/NULLIF(a.employee_count,0) AS cost_per_employee
          FROM actual a JOIN warehouse.budget_payroll_dept_month b USING(month,department_id)
          LEFT JOIN warehouse.dim_department d USING(department_id)""")
        c.execute("""CREATE OR REPLACE VIEW metrics.t10_kpi_scorecard AS
          WITH att AS (SELECT date_trunc('month',period_end_date)::DATE AS month,department_id,
            SUM(present_days+0.5*half_days_unpaid)/NULLIF(SUM(scheduled_days),0) AS attendance_rate
            FROM warehouse.fact_attendance_monthly GROUP BY 1,2 HAVING COUNT(DISTINCT employee_id)>=5),
          pay AS (SELECT date_trunc('month',period_end_date)::DATE AS month,department_id,
            100.0*SUM(overtime_pay)/NULLIF(SUM(employer_cost),0) AS overtime_share_pct
            FROM warehouse.fact_payroll GROUP BY 1,2 HAVING COUNT(DISTINCT employee_id)>=5),
          task AS (SELECT date_trunc('month',s.end_date)::DATE AS month,t.team_id,tm.department_id,
            100.0*COUNT(*) FILTER(WHERE upper(t.status)='DONE')/NULLIF(COUNT(*) FILTER(WHERE upper(t.status)<>'CANCELLED'),0) AS task_completion_pct
            FROM warehouse.fact_task t JOIN warehouse.dim_sprint s USING(sprint_id) JOIN warehouse.dim_team tm USING(team_id)
            GROUP BY 1,2,3),
          task_month AS (SELECT month,department_id,AVG(task_completion_pct) AS task_completion_pct
            FROM task GROUP BY 1,2),
          attr AS (SELECT month_start_date AS month,department_id,
            100.0*SUM(exits)/NULLIF(SUM(headcount_start),0) AS attrition_pct
            FROM warehouse.fact_headcount_monthly GROUP BY 1,2)
          SELECT k.month,k.department_id,d.department_name,
            a.attendance_rate,k.attendance_rate_target,
            CASE WHEN a.attendance_rate IS NULL THEN 'No data' WHEN a.attendance_rate>=k.attendance_rate_target THEN 'Green' ELSE 'Red' END AS attendance_status,
            p.overtime_share_pct,k.overtime_share_target_pct,
            CASE WHEN p.overtime_share_pct IS NULL THEN 'No data' WHEN p.overtime_share_pct<=k.overtime_share_target_pct THEN 'Green' ELSE 'Red' END AS overtime_status,
            k.attrition_monthly_target_pct,k.task_completion_target_pct,
            x.task_completion_pct,
            a2.attrition_pct,
            CASE WHEN a2.attrition_pct IS NULL THEN 'No data' WHEN a2.attrition_pct<=k.attrition_monthly_target_pct THEN 'Green' ELSE 'Red' END AS attrition_status,
            CASE WHEN x.task_completion_pct IS NULL THEN 'No data' WHEN x.task_completion_pct>=k.task_completion_target_pct THEN 'Green' ELSE 'Red' END AS completion_status
          FROM warehouse.kpi_targets k LEFT JOIN att a USING(month,department_id)
          LEFT JOIN pay p USING(month,department_id) LEFT JOIN task_month x USING(month,department_id)
          LEFT JOIN attr a2 USING(month,department_id)
          LEFT JOIN warehouse.dim_department d USING(department_id)""")
        print("Loaded warehouse.budget_payroll_dept_month and warehouse.kpi_targets; created metrics.t10_budget_variance and metrics.t10_kpi_scorecard.")

if __name__=="__main__": main()
