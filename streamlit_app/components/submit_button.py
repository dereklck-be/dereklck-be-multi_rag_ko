import streamlit as st


def submit_button_with_state(label, on_click):
    return st.button(label, on_click=on_click, disabled=st.session_state.get("is_processing", False))
