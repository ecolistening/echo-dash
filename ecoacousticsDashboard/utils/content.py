import os
from pathlib import Path

from dash import html
from loguru import logger

CONTENT_PATH = Path(Path.cwd(), 'content')
def get_content_file(name):
    file_path = Path(CONTENT_PATH, name)
    if not os.path.isfile(file_path):
        logger.warning(f"Cannot find \'{file_path}\'")
        return None
    return file_path

def get_content_text(name):
    file_path = get_content_file(name)

    if file_path is None:
        return ""

    content = []
    text = ""

    with open(file_path) as this_file:
        for a in this_file.read():
            if "\n" in a:
                content.append(text)
                content.append(html.Br())
                text = ""
            else:
                text += a
    content.append(text)

    return content