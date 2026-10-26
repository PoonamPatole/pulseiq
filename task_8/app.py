"""Task 8: team delivery metrics by sprint."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DB=Path(__file__).resolve().parent.parent/"pulseiq.duckdb"
st.set_page_config(page_title="Task 8 | Teams",layout="wide")
st.title("Task 8 | Team productivity")
st.markdown("**Rules:** velocity = completed story points; cycle time = mean nonnegative days for completed tasks; on-time = on-time completions / completions. Cancelled tasks are excluded from completion rate; velocity and cycle time only include completed tasks.")
@st.cache_data(ttl=60)
def read(sql,params=()):
 with duckdb.connect(str(DB),read_only=True) as c:return c.execute(sql,list(params)).df()
try:
 teams=read("SELECT team_id,team_name FROM warehouse.dim_team ORDER BY team_name")
 sprints=read("SELECT sprint_id,sprint_name,start_date FROM warehouse.dim_sprint ORDER BY start_date")
except Exception as e: st.error(f"Build Tasks 1–4 first. {e}"); st.stop()
choice=st.sidebar.selectbox("Sprint",sprints.sprint_id.tolist(),format_func=lambda x:sprints.set_index('sprint_id').loc[x,'sprint_name'])
df=read("""SELECT t.team_id,tm.team_name,t.sprint_id,
  SUM(t.story_points) FILTER(WHERE upper(t.status)='DONE') AS velocity,
  AVG(t.cycle_time_days) FILTER(WHERE upper(t.status)='DONE' AND t.cycle_time_days>=0) AS cycle_days,
  COUNT(*) FILTER(WHERE upper(t.status)='DONE' AND upper(t.completed_on_time)='Y')*100.0/NULLIF(COUNT(*) FILTER(WHERE upper(t.status)='DONE'),0) AS on_time_pct,
  COUNT(*) FILTER(WHERE upper(t.status)='BLOCKED') AS blocked,
  SUM(COALESCE(t.reopened_count,0)) AS reopened,
  COUNT(*) FILTER(WHERE upper(t.status)<>'CANCELLED') AS active_tasks,
  COUNT(*) FILTER(WHERE upper(t.status)='DONE') AS done_tasks
 FROM warehouse.fact_task t LEFT JOIN warehouse.dim_team tm USING(team_id)
 GROUP BY 1,2,3 ORDER BY 2""",( ))
all_sprints=st.checkbox("Compare all sprints",value=False)
shown=df if all_sprints else df[df.sprint_id==choice]
st.plotly_chart(px.bar(shown,x="team_name",y="velocity",color="sprint_id",barmode="group",title="Completed story points"),use_container_width=True)
left,right=st.columns(2)
left.plotly_chart(px.bar(shown,x="team_name",y="on_time_pct",color="sprint_id",barmode="group",title="On-time delivery (%)"),use_container_width=True)
right.plotly_chart(px.bar(shown,x="team_name",y="blocked",color="sprint_id",barmode="group",title="Blocked tasks"),use_container_width=True)
st.dataframe(shown,hide_index=True,use_container_width=True)
st.caption("Compare teams with their team size, work type and sprint length in mind. A high velocity alone does not establish team health.")
st.subheader("Three observations for the selected sprint")
for col,label,fmt in [("velocity","highest velocity","{:.0f} points"),("cycle_days","longest average cycle","{:.1f} days"),("reopened","most reopened items","{:.0f} reopened")]:
 if shown[col].notna().any():
  r=shown.loc[shown[col].idxmax()]; st.write(f"{r.team_name} has the {label}: {fmt.format(r[col])}.")
st.info("Hand-check template: select two teams, filter fact_task to the chosen sprint and team, then count completed story points and completed tasks directly. Record both values in evidence/verification.md.")
