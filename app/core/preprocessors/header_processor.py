import re
import logging
from app.core.utils.progress_utils import get_tqdm

logger = logging.getLogger(__name__)


def extract_headers_and_text(page_text):
    header_pattern = re.compile(r"^\d+\.\d+ .+$")
    text_blocks = []
    lines = page_text.split('\n')

    with get_tqdm(total=len(lines), desc="Extracting headers and text") as pbar:
        for line in lines:
            if header_pattern.match(line):
                text_blocks.append(f"### {line}")
                logger.debug(f"Extracted header: {line}")
            else:
                text_blocks.append(line)
            pbar.update(1)

    return '\n'.join(text_blocks)