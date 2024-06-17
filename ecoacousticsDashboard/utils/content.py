from pathlib import Path
from dash import html

CONTENT_PATH = Path(Path.cwd(), 'content')
def get_content_file(name):
    return Path(CONTENT_PATH, name)

def get_content_text(name):
    content_path = get_content_file(name)

    content = []
    text = ""

    with open(content_path) as this_file:
        for a in this_file.read():
            if "\n" in a:
                content.append(text)
                content.append(html.Br())
                text = ""
            else:
                text += a
    content.append(text)

    return content