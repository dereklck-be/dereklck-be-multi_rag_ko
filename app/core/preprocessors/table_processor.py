import logging
import pandas as pd

logger = logging.getLogger(__name__)


def extract_table(page):
    table = page.extract_table()

    if table is not None:
        df = pd.DataFrame(table[1:], columns=table[0])
        markdown_table = df.to_markdown(index=False)
        logger.debug(f"Extracted table from page {page.page_number}: {markdown_table}")
        return markdown_table

    return None
