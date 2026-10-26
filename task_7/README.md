# Task 7 — Attrition analytics

Run: `..\.venv\Scripts\python.exe -m streamlit run .\task_7\app.py`.

Actual exits use M03/M04-style monthly warehouse totals. Voluntary exit totals are shown separately. The supplied monthly fact has no other exit-type breakdown. Tenure is calculated from hire and exit dates, aggregated by department and suppressed below five exits. The prediction section is visibly labelled and suppresses groups with fewer than five people; it never selects names or individual scores.

The three largest monthly department exit counts are printed with their attrition rates. For a department with four people, the app omits the risk group because it could expose an individual.
