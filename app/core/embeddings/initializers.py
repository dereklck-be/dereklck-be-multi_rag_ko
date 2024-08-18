import logging
from typing import Optional
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from app.repositories.text_repository import TextRepository

logger = logging.getLogger(__name__)


def get_ko_sbert_nli_embedding():
    model_name = "upskyy/kf-deberta-multitask"
    encode_kwargs = {'normalize_embeddings': True}
    ko_embedding = HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs=encode_kwargs
    )
    return ko_embedding


async def initialize_bm25_retriever(collection_name: str, repository_path: str) -> Optional[BM25Retriever]:
    try:
        text_repo = TextRepository(repository_path)
        all_documents = text_repo.load_documents(collection_name)

        logger.info(f"Number of documents loaded for collection '{collection_name}': {len(all_documents)}")

        if not all_documents:
            logger.warning("No documents found for BM25 retriever initialization.")
            return None

        preprocessed_docs = [Document(page_content=doc.page_content, metadata=doc.metadata) for doc in all_documents]
        bm25_retriever = BM25Retriever.from_documents(
            documents=preprocessed_docs,
            similarity_top_k=8,
            language="korean"
        )

        logger.info(f"BM25 retriever initialized with {len(preprocessed_docs)} documents")
        return bm25_retriever
    except Exception as e:
        logger.error(f"Error initializing BM25 retriever: {e}", exc_info=True)
        return None