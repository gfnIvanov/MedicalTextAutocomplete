import os
import traceback
import logging
from pathlib import Path
from typing import Iterator
from selenium import webdriver
from selenium.webdriver.common.by import By

CURRENT_DIR = Path(__file__).resolve().parent
LOG = logging.getLogger(__name__)

def cr_parser(url: str, code: str) -> Iterator[str]:
    try:
        driver = webdriver.Firefox()
        driver.get(f"{url}/{code}")

        driver.implicitly_wait(5)

        text_blocks = driver.find_elements(By.CLASS_NAME, "clin-rec-doc__content")
        for block in text_blocks:
            for paragraph in block.find_elements(By.CSS_SELECTOR, "p, ul, ol"):
                if paragraph.get_property("parentNode").tag_name != 'td':
                    text = paragraph.text
                    if text.strip() != "" and len(text.split(" ")) > 2:
                        yield paragraph.text

        driver.quit()
    except Exception as err:
        driver.quit()
        LOG.error(err)
        if os.getenv("MODE") == "dev":
            traceback.print_tb(err.__traceback__)
