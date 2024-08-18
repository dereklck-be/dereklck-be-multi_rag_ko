import os
import asyncio
import logging
from typing import List
from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class ChromaRepository:
    def __init__(self, collection_name: str, chroma_directory: str):
        self.ko_embedding = HuggingFaceEmbeddings(model_name="upskyy/kf-deberta-multitask")
        self.collection_name = collection_name
        self.persist_directory = f"{chroma_directory}/{collection_name}"
        os.makedirs(self.persist_directory, exist_ok=True)
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.ko_embedding,
            collection_name=collection_name,
            collection_metadata={"hnsw:space": "cosine"}
        )
        self.retriever = self.vectorstore.as_retriever()

    async def add_documents(self, doc_chunks: List[Document]):
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.vectorstore.add_documents, doc_chunks)
            logger.debug(f"Added {len(doc_chunks)} documents to {self.collection_name}")
        except Exception as e:
            logger.error(f"Error in add_documents: {e}", extra={"collection_name": self.collection_name})
            raise HTTPException(status_code=500, detail=str(e))

    async def get_relevant_documents(self, query: str, top_k=10) -> List[Document]:
        try:
            logger.info(f"Searching in {self.collection_name} for query: {query}")
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, self.vectorstore.similarity_search_with_score, query, top_k)
            docs_with_scores = [
                Document(page_content=doc.page_content, metadata={**doc.metadata, 'cosine_similarity': 1 - distance})
                for doc, distance in results
            ]

            logger.info(f"Chroma retrieved {len(docs_with_scores)} documents")

            return docs_with_scores
        except Exception as e:
            logger.error(f"Error in get_relevant_documents: {e}", extra={"collection_name": self.collection_name})
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_documents(self) -> List[Document]:
        try:
            query = ""  # empty query to fetch all documents
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, self.vectorstore.similarity_search_with_score, query, 1000)
            documents = [Document(page_content=doc.page_content, metadata=doc.metadata) for doc, _ in results]
            logger.info(f"Loaded {len(documents)} documents from {self.collection_name}")
            return documents
        except Exception as e:
            logger.error(f"Error in get_all_documents: {e}", extra={"collection_name": self.collection_name})
            raise HTTPException(status_code=500, detail=str(e))
