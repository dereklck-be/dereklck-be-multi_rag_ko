import logging
from app.models.state import AppState
from fastapi import APIRouter, Request
from app.services.search_service import SearchService
from app.core.utils.response_handler import success_handler, error_handler

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search_data")
async def search_vector(payload: dict, request: Request):
    query = payload.get("query")
    collection_name = payload.get("collection_name")

    if not query or not collection_name:
        logger.warning("Query and collection_name must be provided")
        return error_handler("Query and collection_name must be provided", status_code=400)

    logger.info(f"API search_vector called with query: {query} in collection: {collection_name}")
    app_state: AppState = request.app.state.app_state

    if not app_state.bm25_retriever:
        logger.error("BM25 retriever is not initialized")
        return error_handler("BM25 retriever is not initialized", status_code=500)

    try:
        search_service = SearchService(collection_name, query, app_state)
        result = await search_service.get_relevant_documents()

        if result["status"] == "error":
            error_message = result["message"] if isinstance(result["message"], str) else "An error occurred"
            return error_handler(error_message, status_code=404)

        return success_handler(result, status_code=200)
    except Exception as e:
        logger.error(f"Exception in search_vector: {str(e)}", exc_info=True)
        return error_handler(e, status_code=500)