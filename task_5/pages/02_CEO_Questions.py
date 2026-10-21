import streamlit as st


st.set_page_config(page_title="CEO Questions | PulseIQ", page_icon="◼", layout="wide")
st.title("Five CEO questions")
st.caption("The workforce page is designed to answer these questions at a glance.")

questions = [
    ("How many people are in the workforce?", "Headcount at the end of the selected month."),
    ("Is headcount growing or shrinking?", "The trend and selected-period change show direction and size."),
    ("Which departments have the most people?", "The department mix compares reportable department groups."),
    ("Where are employees located by city tier?", "Location-tier mix shows the distribution of visible headcount."),
    ("How do employees work?", "The work-mode chart compares visible work-mode groups."),
]

for i, (question, answer) in enumerate(questions, start=1):
    st.markdown(f"**{i}. {question}**  \n{answer}")

st.divider()
st.subheader("Metric and privacy notes")
st.markdown(
    "- Headcount trend and cards use the governed M01 metric.\n"
    "- Department, location-tier, and work-mode charts query aggregate views in the `metrics` schema.\n"
    "- The dashboard does not query raw or warehouse tables.\n"
    "- Groups below the configured minimum size are omitted. The current workbook contains unresolved Task 3 findings, so treat affected source metrics as provisional."
)
