import streamlit as st


def render_sidebar():
    st.sidebar.header("Data Ingestion")
    uploaded_files = st.sidebar.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True,
        disabled=st.session_state.get("lock_widgets", False)
    )
    collection_name = st.sidebar.text_input(
        "Enter collection name for ingestion:",
        disabled=st.session_state.get("lock_widgets", False)
    )
    ingest_button = st.sidebar.button(
        "Ingest Files",
        disabled=st.session_state.get("lock_widgets", False)
    )
    return uploaded_files, collection_name, ingest_button


def render_main_content():
    st.title("Multi RAG Chatbot")
    st.header("Ask a Question")
    user_query = st.text_input(
        "Enter your query:",
        key="user_query",
        disabled=st.session_state.get("lock_widgets", False)
    )
    return user_query
