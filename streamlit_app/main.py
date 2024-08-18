import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from streamlit_app.templates.layout import render_sidebar, render_main_content
from streamlit_app.components.submit_button import submit_button_with_state
from streamlit_app.utils.request_handler import get_answer_from_api, ingest_files
from streamlit_app.config import BASE_URL

env_path = Path(__file__).resolve().parent / '.env.local'
print(f"Loading environment variables from {env_path}")
load_dotenv(dotenv_path=env_path)

api_url = f"{BASE_URL}"


def is_backend_ready(base_url):
    try:
        response = requests.get(f"{base_url}/healthcheck")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Backend health check failed: {e}")
        return False


while not is_backend_ready(api_url):
    st.warning("Waiting for backend to be ready...")
    time.sleep(1)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False

if "lock_widgets" not in st.session_state:
    st.session_state["lock_widgets"] = False

if "user_query" not in st.session_state:
    st.session_state["user_query"] = ""

if "collection_name" not in st.session_state:
    st.session_state["collection_name"] = ""

uploaded_files, collection_name, ingest_button = render_sidebar()

if ingest_button:
    st.session_state["is_processing"] = True
    st.session_state["lock_widgets"] = True
    st.session_state["collection_name"] = collection_name

    with st.spinner('데이터 전처리 진행 중입니다. 업로드한 파일을 삭제하지 말아주십시오.'):
        message = ingest_files(uploaded_files, collection_name)

    if "Validation failed" not in message:
        st.toast(message)

    st.session_state["is_processing"] = False
    st.session_state["lock_widgets"] = False


def handle_submit():
    query = st.session_state["user_query"]
    if query and not st.session_state["is_processing"]:
        st.session_state["is_processing"] = True
        st.session_state["previous_query"] = query
        st.session_state["user_query"] = ""

        with st.spinner('답변을 생성 중입니다...'):
            answer = get_answer_from_api(query, st.session_state["chat_history"], st.session_state["collection_name"])

        if answer == "Error occurred while fetching the answer.":
            st.toast("Ingest를 먼저 진행해주세요.", icon="⚠️")
        else:
            st.session_state["chat_history"].append({"role": "user", "content": query})
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})

        st.session_state["is_processing"] = False
        st.session_state["lock_widgets"] = False


user_query = render_main_content()
submit_button_with_state("Submit", handle_submit)

if st.session_state["collection_name"]:
    st.sidebar.info(f"현재 참조 중인 컬렉션: {st.session_state['collection_name']}")

st.markdown("### Chat History")
for i in range(len(st.session_state["chat_history"]) // 2, 0, -1):
    user_entry = st.session_state["chat_history"][2 * (i - 1)]
    assistant_entry = st.session_state["chat_history"][2 * (i - 1) + 1]
    st.markdown(f"**User:** {user_entry['content']}")
    st.markdown(f"**Assistant:** {assistant_entry['content']}")
    st.markdown("---")

if st.session_state["lock_widgets"]:
    st.markdown(
        """
        <style>
        #root { pointer-events: none; opacity: 0.6; }
        section[data-testid="stSidebar"], .main { pointer-events: none; opacity: 0.6; }
        </style>
        """,
        unsafe_allow_html=True
    )