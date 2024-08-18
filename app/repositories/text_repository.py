import os
import json
import logging
from typing import List
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class TextRepository:
    def __init__(self, repository_path: str) -> None:
        self.repository_path = repository_path
        os.makedirs(self.repository_path, exist_ok=True)

    def save_documents(self, documents: List[Document], collection_name: str) -> None:
        file_path = os.path.join(self.repository_path, f"{collection_name}.jsonl")

        existing_documents = self.load_documents(collection_name)
        existing_docs_set = set(
            (doc.page_content, json.dumps(doc.metadata, sort_keys=True)) for doc in existing_documents)

        with open(file_path, "a", encoding="utf-8") as f:
            for doc in documents:
                json_doc = json.dumps(
                    {"page_content": doc.page_content, "metadata": doc.metadata},
                    ensure_ascii=False
                )

                if (doc.page_content, json.dumps(doc.metadata, sort_keys=True)) not in existing_docs_set:
                    f.write(json_doc + "\n")
        logger.info(f"Saved {len(documents)} documents in {file_path}")

    def load_documents(self, collection_name: str) -> List[Document]:
        file_path = os.path.join(self.repository_path, f"{collection_name}.jsonl")
        if not os.path.exists(file_path):
            return []

        documents = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                json_doc = json.loads(line)
                documents.append(Document(page_content=json_doc["page_content"], metadata=json_doc["metadata"]))

        logger.info(f"Loaded {len(documents)} documents from {file_path}")
        return documents
