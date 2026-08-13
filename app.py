import streamlit as st

st.set_page_config(
    page_title="Top AI Factory Analysis",
    page_icon=":bar_chart:",
    layout="wide",
)

with st.sidebar:
    st.markdown("## Agentic Control Panel")
    st.write("UI placeholder")
    st.write("Agent logic will be added later by the team.")

st.title("Top AI Factory Analysis")
st.write("Hello world. The Streamlit app is connected and ready for future agent integration.")

st.markdown("### Current Setup")
st.write("- `schema.py` is ready and should stay shared across the whole team.")
st.write("- `agents/` files are placeholders with instructions for each assigned member.")
st.write("- `app.py` is intentionally simple for now.")

st.info("Next step: each groupmate adds code only inside their assigned agent file.")
