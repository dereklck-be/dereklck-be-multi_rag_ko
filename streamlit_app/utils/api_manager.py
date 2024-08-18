import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path(__file__).resolve().parent.parent / '.env.local'
load_dotenv(dotenv_path=env_path)

# FastAPI 서버의 기본 URL
BACKEND_HOST = os.getenv('BACKEND_HOST', '127.0.0.1')
BACKEND_PORT = os.getenv('BACKEND_PORT', '8000')
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"


class APIManager:
    @staticmethod
    def get_answer_endpoint() -> str:
        return f"{BASE_URL}/api/v1/answer/answer-question"

    @staticmethod
    def ingest_data_endpoint() -> str:
        return f"{BASE_URL}/api/v1/ingest/ingest_data"
