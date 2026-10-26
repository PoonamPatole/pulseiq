# Task 6 — Attendance and leave

Run from the project root: `..\.venv\Scripts\python.exe -m streamlit run .\task_6\app.py`.

Attendance rate is (present days + half of unpaid half days) / scheduled days, matching M13. Late arrivals are divided by present days; overtime is summed in hours. Leave is approved requests only and company-wide because the leave fact has no department key. Holiday counts come from `dim_date`; a holiday is context, not proof of cause. The app prints the three lowest observed monthly attendance rates with values for review.

The source data has monthly summaries, so the chart cannot reliably label long weekends. Department is a real filter for attendance and a company-wide leave limitation is disclosed.
