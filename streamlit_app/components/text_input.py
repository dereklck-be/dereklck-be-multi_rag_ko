import streamlit as st


def get_user_query() -> str:
    st.markdown("### Ask a Question")
    query = st.text_input("Enter your query:", key="user_query",
                          disabled=st.session_state.get("queries_in_progress", False))
    return query
