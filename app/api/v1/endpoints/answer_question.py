import logging
from typing import Optional
from fastapi import APIRouter, Query
from app.services.answer_service import AnswerService
from app.core.utils.response_handler import success_handler, error_handler

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/answer_question")
async def answer_question(
        payload: dict,
        model_name: Optional[str] = Query("gpt-3.5-turbo"),
        collection_name: Optional[str] = Query(...)):
    try:
        query = payload.get("query")
        if not query:
            return error_handler("Query must be provided", status_code=400)

        chat_history = payload.get("chat_history", [])
        if not chat_history:
            chat_history = []

        logger.info("Received query: %s", query)
        service = AnswerService(model_name=model_name)
        result = await service.get_answer(query, chat_history, collection_name)
        logger.info(f"Result: {result}")

        return success_handler({"message": result}, status_code=200)
    except Exception as e:
        logger.error("Error processing data: %s", str(e))
        return error_handler(e, status_code=500)