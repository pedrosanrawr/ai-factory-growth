import streamlit as st

from frontend.page import render_app


st.set_page_config(
    page_title="Top AI Factory Analysis",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_app()
