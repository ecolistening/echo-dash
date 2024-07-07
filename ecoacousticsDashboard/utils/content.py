import os
from pathlib import Path

from dash import html, dcc, callback, Input, State, Output
from loguru import logger

CONTENT_PATH = Path(Path.cwd(), 'content')
def get_content_file(name):
    file_path = Path(CONTENT_PATH, name)
    if not os.path.isfile(file_path):
        logger.warning(f"Cannot find \'{file_path}\'")
        return None
    return file_path

def get_content_text(name):
    if not '.' in name:
        name = name+'.txt'
    file_path = get_content_file(name)

    if file_path is None:
        logger.warning(f"File \'{name}\' not found.")
        return ["No text found."]

    content = []
    text = ""

    hash_c = 0
    make_title = False

    with open(file_path) as this_file:
        for a in this_file.read():

            # Count hash for 
            if text=='' and a=='#':
                hash_c += 1
                continue
            elif not make_title and hash_c > 0:
                make_title = True

            if "\n" in a:
                if text != '':
                    if make_title:
                        if hash_c == 1: title=html.H1(text)
                        elif hash_c == 2: title=html.H2(text)
                        elif hash_c == 3: title=html.H3(text)
                        elif hash_c > 3: title=html.H4(text)
                        content.append(title)
                        hash_c = 0
                        make_title = False
                    else:
                        content.append(text)
                if not make_title: content.append(html.Br())
                text = ""
            else:
                text += a
    
    if text != '':
        if make_title:
            if hash_c == 1: title=html.H1(text)
            elif hash_c == 2: title=html.H2(text)
            elif hash_c == 3: title=html.H3(text)
            elif hash_c > 3: title=html.H4(text)
            content.append(title)
            hash_c = 0
            make_title = False
        else:
            content.append(text)

    logger.debug(f"Return content for {name}: {len(content)} elements.")
    return content

def get_tabs(pagename,about=True,feature=True,dataset=True):
    tabs = []
    if about:
        tabs.append(dcc.Tab(label='About', value='about'))
    if feature:
        tabs.append(dcc.Tab(label='Descriptor', value='feature'))
    if dataset:
        tabs.append(dcc.Tab(label='Dataset', value='dataset'))

    tab_div = html.Div([
        dcc.Tabs(id=f'tabs-{pagename}', value='about', children=tabs),
        html.Div(id=f'tabs-{pagename}-content')
    ])

    @callback(
        Output(f'tabs-{pagename}-content', 'children'),
        Input(f'tabs-{pagename}', 'value'),
        Input('dataset-select', component_property='value'),
        Input('feature-dropdown', component_property='value')
    )
    def render_content(tab,dataset,feature):
        if tab == 'about':
            return html.Div(get_content_text(f"page/{pagename}"))
        elif tab == 'feature':
            return html.Div(get_content_text(f"feature/{feature}"))
        elif tab == 'dataset':
            return html.Div(get_content_text(f"dataset/{dataset}"))
    return tab_div