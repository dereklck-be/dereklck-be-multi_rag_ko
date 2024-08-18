# search_service.py

import logging
from typing import List, Dict
from app.config import settings
from fastapi import HTTPException
from app.models.state import AppState
from app.repositories.chroma_repository import ChromaRepository
from app.core.utils.common import (
    context_reorder_documents,
    map_reordered_docs,
    combine_results,
    log_json_docs,
    empty_result,
    log_documents
)

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, collection_name: str, query: str, app_state: AppState):
        self.collection_name = collection_name
        self.query = query
        self.app_state = app_state
        chroma_repo = ChromaRepository(collection_name, chroma_directory=settings.CHROMA_DIRECTORY)
        self.chroma_retriever = chroma_repo.retriever
        self.bm25_retriever = self.app_state.bm25_retriever
        if not self.bm25_retriever:
            logger.error("BM25 retriever is not initialized")
            raise HTTPException(status_code=500, detail="BM25 retriever is not initialized")

    async def get_relevant_documents(self, top_k: int = 8) -> Dict[str, List[Dict]]:
        try:
            logger.info(f"Searching for query: '{self.query}' with top_k: {top_k}")
            dense_results = await self.chroma_retriever.aget_relevant_documents(query=self.query, k=top_k // 2)
            logger.info(f"Dense Results fetched: {len(dense_results)}")

            bm25_all_results = self.bm25_retriever.get_relevant_documents(query=self.query)
            logger.info(f"BM25 All Results fetched: {len(bm25_all_results)}")
            bm25_results = bm25_all_results[:top_k // 2]
            logger.info(f"BM25 Top Results: {len(bm25_results)}")

            dense_documents = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in dense_results]
            bm25_documents = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in bm25_results]

            log_documents(dense_documents, "Dense")
            log_documents(bm25_documents, "BM25")

            reordered_dense_docs = context_reorder_documents(dense_documents)
            reordered_dense_results = map_reordered_docs(reordered_dense_docs, dense_results)
            combined_results = combine_results(reordered_dense_results, bm25_results, top_k)

            if not combined_results:
                return empty_result()

            json_docs = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in combined_results]
            log_json_docs(json_docs)

            return {
                "message": "Documents retrieved successfully.",
                "results": json_docs,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Unhandled error in get_relevant_documents: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))