from typing import List
from app.core.utils.progress_utils import get_tqdm


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 500) -> List[str]:
    words = text.split()
    chunks = []
    pbar_total = len(words) // chunk_size + 1

    with get_tqdm(total=pbar_total, desc="Splitting text into chunks") as pbar:
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            pbar.update(1)

    return chunks
