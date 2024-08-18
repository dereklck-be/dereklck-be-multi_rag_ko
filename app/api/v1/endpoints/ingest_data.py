import logging
from typing import List
from app.config import settings
from app.models.state import initial_app_state
from fastapi import APIRouter, UploadFile, File, Form
from app.core.utils.common import save_files, is_directory_non_empty
from app.core.embeddings.initializers import initialize_bm25_retriever
from app.core.utils.response_handler import success_handler, error_handler
from app.services.ingest_service import process_and_store_vector, process_and_store_text

UPLOAD_DIRECTORY = settings.UPLOAD_DIR
if UPLOAD_DIRECTORY is None:
    raise ValueError("UPLOAD_DIR environment variable is not set")

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/ingest_data")
async def ingest_data(files: List[UploadFile] = File(...), collection_name: str = Form(...)):
    try:
        logger.info(f"Starting data ingestion for collection: {collection_name}")
        file_paths = save_files(files, UPLOAD_DIRECTORY)

        # await process_and_store_vector(file_paths, collection_name)
        # await process_and_store_text(file_paths, collection_name)

        if is_directory_non_empty(settings.TEXT_REPOSITORY_PATH):
            bm25_retriever = await initialize_bm25_retriever(collection_name, settings.TEXT_REPOSITORY_PATH)
            if bm25_retriever:
                initial_app_state.bm25_retriever = bm25_retriever
                logger.info("BM25 retriever successfully initialized after data ingestion.")
            else:
                logger.error("BM25 retriever initialization failed after data ingestion.")
        else:
            logger.error("Text repository path does not contain any files after data ingestion.")

        return success_handler({"message": "Ingesting data completed"})
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return error_handler(e, status_code=500)