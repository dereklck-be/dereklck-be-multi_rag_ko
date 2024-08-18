import re
import tqdm
import logging
import pdfplumber
import numpy as np
from typing import List
from app.config import settings
from fastapi import HTTPException
from langchain_core.documents import Document
from app.core.utils.progress_utils import get_tqdm
from app.core.utils.cache_manager import CacheManager
from app.repositories.text_repository import TextRepository
from app.repositories.chroma_repository import ChromaRepository
from app.core.preprocessors.table_processor import extract_table
from app.core.preprocessors.text_splitter import split_text_into_chunks
from app.core.embeddings.initializers import get_ko_sbert_nli_embedding
from app.core.preprocessors.header_processor import extract_headers_and_text
from app.core.utils.common import validate_collection_name, calculate_cosine_similarity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
cache_manager = CacheManager()


async def process_and_store_vector(files: List[str], collection_name: str) -> None:
    try:
        collection_name = validate_collection_name(collection_name)
        chroma_repo = ChromaRepository(collection_name, settings.CHROMA_DIRECTORY)
        ko_embedding = get_ko_sbert_nli_embedding()
        total_files = len(files)

        with get_tqdm(total=total_files, desc="Processing vector files") as pbar:
            for file_path in files:
                try:
                    await process_file_vector(file_path, chroma_repo, ko_embedding)
                    logger.info(f"Finished processing vector for file: {file_path}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Error in process_and_store_vector: {e}", extra={'file_path': file_path})
                    raise HTTPException(status_code=500, detail=str(e))
                finally:
                    cache_manager.clear_cache()
                    logger.info("Cache cleared after ingestion process.")
    except Exception as e:
        logger.error(f"Unhandled error in process_and_store_vector: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_and_store_text(files: List[str], collection_name: str, chunk_size: int = 200) -> None:
    try:
        collection_name = validate_collection_name(collection_name)
        text_repo = TextRepository(settings.TEXT_REPOSITORY_PATH)
        total_files = len(files)

        with get_tqdm(total=total_files, desc="Processing text files") as pbar:
            for file_path in files:
                try:
                    await process_file_text(file_path, text_repo, collection_name, chunk_size)
                    logger.info(f"Finished processing text for file: {file_path}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Error in process_and_store_text: {e}", extra={'file_path': file_path})
                    raise HTTPException(status_code=500, detail=str(e))
                finally:
                    cache_manager.clear_cache()
                    logger.info("Cache cleared after ingestion process.")
    except Exception as e:
        logger.error(f"Unhandled error in process_and_store_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_file_text(file_path: str, text_repo: TextRepository, collection_name: str,
                            chunk_size: int = 200) -> None:
    try:
        if not file_path:
            raise ValueError("File path must be provided")
        logger.info(f"Processing file (text): {file_path}")
        text = extract_text_from_pdf(file_path)
        tokens = tokenize_text(text)
        logger.info(f"Tokenized text into {len(tokens)} tokens")
        chunks = create_text_chunks(tokens, chunk_size)
        logger.info(f"Created {len(chunks)} chunks of size {chunk_size}")
        total_chunks = len(chunks)

        with get_tqdm(total=total_chunks, desc=f"Processing {file_path}") as pbar:
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
                document = Document(page_content=' '.join(chunk), metadata={"source": f"{file_path}_chunk_{i + 1}"})
                text_repo.save_documents([document], collection_name)
                pbar.update(1)
        logger.info(f"Total chunks processed: {len(chunks)}")
    except Exception as e:
        logger.error(f"Error in process_file_text: {e}", extra={'file_path': file_path})
        raise HTTPException(status_code=500, detail=str(e))


def extract_text_from_pdf(file_path: str) -> str:
    try:
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            complete_text = []

            with get_tqdm(total=page_count, desc=f"Extracting text from {file_path}", dynamic_ncols=True) as pbar:
                for pdf_page in pdf.pages:
                    text = pdf_page.extract_text()
                    if text:
                        complete_text.append(text)
                    pbar.update(1)
            logger.info(f"Extracted text from PDF: {len(complete_text)} pages found")
        return ' '.join(complete_text)
    except Exception as e:
        logger.error(f"Error in extract_text_from_pdf: {e}", extra={'file_path': file_path})
        raise HTTPException(status_code=500, detail=str(e))


def tokenize_text(text: str) -> List[str]:
    try:
        tokens = re.findall(r'\b\w+\b', text)
        logger.info(f"Tokenized text, number of tokens: {len(tokens)}")
        return tokens
    except Exception as e:
        logger.error(f"Error in tokenize_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_text_chunks(tokens: List[str], chunk_size: int) -> List[List[str]]:
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
    logger.info(f"Generated {len(chunks)} chunks of size {chunk_size} each.")
    return chunks


async def process_file_vector(file_path: str, chroma_repo: ChromaRepository, ko_embedding) -> None:
    try:
        if not file_path:
            raise ValueError("File path must be provided")
        logger.info(f"Processing file: {file_path}")
        complete_text = extract_text_and_tables(file_path)

        chunks = split_text_into_chunks(complete_text, chunk_size=500, overlap=50)

        total_chunks = len(chunks)
        page_count = len(pdfplumber.open(file_path).pages)

        with get_tqdm(total=total_chunks + page_count, desc=f"Processing {file_path}", dynamic_ncols=True) as pbar:
            await process_chunks_vector(chunks, file_path, ko_embedding, chroma_repo, pbar)
    except Exception as e:
        logger.error(f"Error in process_file_vector: {e}", extra={'file_path': file_path})
        raise HTTPException(status_code=500, detail=str(e))


def extract_text_and_tables(file_path: str) -> str:
    try:
        complete_text = []
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)

            with get_tqdm(total=page_count, desc=f"Extracting text and tables from {file_path}",
                          dynamic_ncols=True) as pbar:
                for page_num, pdf_page in enumerate(pdf.pages):
                    text = pdf_page.extract_text()
                    if text:
                        page_text = extract_headers_and_text(text)
                        complete_text.append(page_text)
                        cache_manager.add_to_cache(f"{file_path}_page_{page_num}", page_text)
                    markdown_table = extract_table(pdf_page)
                    if markdown_table:
                        table_text = f"\nTable extracted from page {page_num}:\n{markdown_table}\n"
                        complete_text.append(table_text)
                        cache_manager.add_to_cache(f"{file_path}_page_{page_num}_table", table_text)
                    pbar.update(1)
        return '\n'.join(complete_text)
    except Exception as e:
        logger.error(f"Error in extract_text_and_tables: {e}", extra={'file_path': file_path})
        raise HTTPException(status_code=500, detail=str(e))


def split_text_into_chunks_with_logging(complete_text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    try:
        chunks = split_text_into_chunks(complete_text, chunk_size, overlap)

        logger.info(f"Split text into {len(chunks)} chunks of size {chunk_size} with an overlap of {overlap}.")
        return chunks
    except Exception as e:
        logger.error(f"Error in split_text_into_chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_chunks_vector(chunks: List[str], file_path: str, ko_embedding, chroma_repo: ChromaRepository,
                                pbar: tqdm.tqdm) -> None:
    try:
        for chunk_index, chunk in enumerate(chunks):
            embeddings = ko_embedding.embed_documents([chunk])
            embeddings = np.array(embeddings)
            cosine_similarity = calculate_cosine_similarity(embeddings)
            doc_obj = Document(
                page_content=chunk,
                metadata={"source": file_path, "cosine_similarity": cosine_similarity[0][0]}
            )
            await chroma_repo.add_documents([doc_obj])
            pbar.update(1)
            logger.debug(f"Processed and stored chunk {chunk_index + 1}/{len(chunks)} from file: {file_path}")
            cache_manager.remove_from_cache(f"{file_path}_page_{chunk_index}")
            cache_manager.remove_from_cache(f"{file_path}_page_{chunk_index}_table")
    except Exception as e:
        logger.error(f"Error in process_chunks_vector: {e}", extra={'file_path': file_path})
        raise HTTPException(status_code=500, detail=str(e))