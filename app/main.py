import uvicorn
import logging
from fastapi import FastAPI
from app.config import settings
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.models.state import initial_app_state, AppState
from app.core.utils.common import is_directory_non_empty
from app.repositories.chroma_repository import ChromaRepository
from app.api.v1.endpoints.ingest_data import router as ingest_data_router_v1
from app.api.v1.endpoints.search_data import router as search_vector_router_v1
from app.api.v1.endpoints.answer_question import router as answer_question_router_v1
from app.core.embeddings.initializers import get_ko_sbert_nli_embedding, initialize_bm25_retriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CustomApp(FastAPI):
    state: AppState


@asynccontextmanager
async def lifespan(app: CustomApp):
    app.state.app_state = initial_app_state
    app.state.app_state.ml_models["ko_sbert_nli_embedding"] = get_ko_sbert_nli_embedding()
    app.state.app_state.chroma_repo = ChromaRepository(collection_name="default",
                                                       chroma_directory=settings.CHROMA_DIRECTORY)

    if is_directory_non_empty(settings.TEXT_REPOSITORY_PATH):
        bm25_retriever = await initialize_bm25_retriever("default", settings.TEXT_REPOSITORY_PATH)
        if bm25_retriever:
            app.state.app_state.bm25_retriever = bm25_retriever
            logger.info("BM25 retriever successfully initialized.")
        else:
            logger.warning("BM25 retriever initialization failed.")
    else:
        logger.warning("Required directories do not contain any files. Please ingest data first.")

    logger.info(f"Chroma persist directory: {app.state.app_state.chroma_repo.persist_directory}")

    try:
        yield
    finally:
        app.state.app_state.ml_models.clear()


app = CustomApp(
    title="LLM RAG Application",
    description="An application to preprocess data, perform RAG pipeline, and provide LLM-based answers",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(answer_question_router_v1, prefix="/api/v1/answer", tags=["v1 Answer Question"])
app.include_router(search_vector_router_v1, prefix="/api/v1/search", tags=["v1 Search Vectors"])
app.include_router(ingest_data_router_v1, prefix="/api/v1/ingest", tags=["v1 Ingest Data"])


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info", access_log=True)
