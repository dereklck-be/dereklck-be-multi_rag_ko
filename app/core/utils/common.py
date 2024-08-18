import os
import re
import logging
import numpy as np
from typing import List
from fastapi import UploadFile
from langchain_community.document_transformers import LongContextReorder

logger = logging.getLogger(__name__)


def calculate_cosine_similarity(embedding):
    if len(embedding.shape) == 1:
        embedding = embedding.reshape(1, -1)
    norms = np.linalg.norm(embedding, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized_embedding = embedding / norms
    cosine_similarity = np.dot(normalized_embedding, normalized_embedding.T)
    return cosine_similarity


def format_collection_name(file_path: str) -> str:
    base_name = os.path.basename(file_path)
    valid_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
    valid_name = re.sub(r'_+', '_', valid_name)
    valid_name = valid_name.strip('_')
    return valid_name


def validate_collection_name(collection_name: str) -> str:
    if not (3 <= len(collection_name) <= 63):
        collection_name = collection_name[:63].rstrip('_')
    if not collection_name[0].isalnum():
        collection_name = 'a' + collection_name[1:]
    if not collection_name[-1].isalnum():
        collection_name = collection_name[:-1] + '1'
    return collection_name


def save_files(files: List[UploadFile], upload_directory: str) -> List[str]:
    logger.info(f"Using UPLOAD_DIRECTORY: {upload_directory}")
    file_paths = []
    os.makedirs(upload_directory, exist_ok=True)
    for file in files:
        file_location = os.path.join(upload_directory, file.filename)
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        file_paths.append(file_location)
    return file_paths


def is_directory_non_empty(directory: str) -> bool:
    return os.path.exists(directory) and len(os.listdir(directory)) > 0


def context_reorder_documents(documents):
    reorder_instance = LongContextReorder()
    return reorder_instance.transform_documents(documents)


def map_reordered_docs(reordered_docs, original_docs):
    reordered_results = []
    for doc in reordered_docs:
        for original_doc in original_docs:
            if original_doc.page_content == doc['page_content']:
                reordered_results.append(original_doc)
                break
    return reordered_results


def combine_results(reordered_dense, bm25_results, top_k):
    return reordered_dense[:top_k // 4] + bm25_results + reordered_dense[top_k // 4: top_k // 2]


def empty_result():
    logger.warning("No relevant documents found.")
    return {
        "message": "No relevant documents found.",
        "status": "error",
        "results": [{"page_content": "", "metadata": {"error": "No relevant documents found"}}]
    }


def log_json_docs(json_docs):
    for i, doc in enumerate(json_docs):
        logger.info(f"Document {i} - Content: {doc['page_content']}, Metadata: {doc['metadata']}")


def log_documents(documents, doc_type):
    print(f"Before Reorder ({doc_type}):")
    for i, doc in enumerate(documents):
        print(f"{doc_type} Document {i + 1}: {doc}")
    print("-" * 50)
