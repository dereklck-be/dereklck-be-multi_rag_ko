import os
from dotenv import load_dotenv

env = os.getenv("ENV", "local")
env_file = f".env.{env}"

load_dotenv(env_file)


class Settings:
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "app/database/pdfs/")
    CHROMA_DIRECTORY: str = os.getenv("CHROMA_DIRECTORY", "app/database/chroma/")
    TEXT_REPOSITORY_PATH: str = os.getenv("TEXT_REPOSITORY_PATH", "app/database/textdb/")


settings = Settings()
