import re
from typing import List
import streamlit as st


def validate_uploaded_files(files: List) -> bool:
    if not files or len(files) == 0:
        st.sidebar.error("Please upload at least one PDF file.")
        return False
    return True


def validate_collection_name(collection_name: str) -> bool:
    if not collection_name:
        st.sidebar.error("Collection name cannot be empty. Please provide a collection name.")
        return False
    if not re.match(r'^[a-zA-Z0-9_]+$', collection_name):
        st.sidebar.error("Collection name must consist of alphanumeric characters and underscores only.")
        return False
    return True


def validate_inputs(files: List, collection_name: str) -> bool:
    return validate_uploaded_files(files) and validate_collection_name(collection_name)
