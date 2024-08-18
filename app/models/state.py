from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from langchain_community.retrievers import BM25Retriever
from app.repositories.chroma_repository import ChromaRepository


class AppState(BaseModel):
    ml_models: Dict[str, Any] = Field(default_factory=dict)
    chroma_repo: Optional[ChromaRepository] = None
    bm25_retriever: Optional[BM25Retriever] = None

    class Config:
        arbitrary_types_allowed = True


initial_app_state = AppState(
    ml_models={},
    chroma_repo=None,
    bm25_retriever=None
)
