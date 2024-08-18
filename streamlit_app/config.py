import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path(__file__).resolve().parent / '.env.local'
print(f"Loading environment variables from {env_path}")
load_dotenv(dotenv_path=env_path)

BACKEND_HOST = os.getenv('BACKEND_HOST', '127.0.0.1')
BACKEND_PORT = os.getenv('BACKEND_PORT', 8000)
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"