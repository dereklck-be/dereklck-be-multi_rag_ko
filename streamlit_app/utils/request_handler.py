import requests
import streamlit as st
from streamlit_app.config import BASE_URL


def get_answer_from_api(query: str, chat_history, collection_name: str):
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/answer/answer_question",
            json={
                "query": query,
                "chat_history": chat_history
            },
            params={
                "collection_name": collection_name
            }
        )
        response.raise_for_status()
        response_data = response.json()
        message = response_data.get("data", {}).get("message", "No answer found.")
        return message
    except requests.RequestException as e:
        st.error(f"Failed to fetch answer: {e}")
        return "Error occurred while fetching the answer."


def ingest_files(files, collection_name):
    if not files or not collection_name:
        st.sidebar.error("Please upload files and provide a collection name.")
        return "Validation failed. Please correct the inputs."

    file_data = []
    for file in files:
        file_data.append(("files", (file.name, file, "application/pdf")))

    if not file_data:
        return "No files to ingest."

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ingest/ingest_data",
            files=file_data,
            data={"collection_name": collection_name}
        )
        response.raise_for_status()
        return response.json().get("message", "Files ingested successfully.")
    except requests.RequestException as e:
        st.error(f"Failed to ingest files: {e}")
        return "Error occurred while ingesting files."
