import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import html, dcc, callback
from dash import Input, Output
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, List, Dict

from api import dispatch, FETCH_DATASETS
from utils import capitalise_each

def Menu():
    pages = {m: m.split('.')[1:] for m in dash.page_registry}
    children = {}
    for p in pages:
        page = dash.page_registry[p]
        if len(pages[p]) == 0:
            logger.warning(f"Can't find page {p}")
            continue
        elif len(pages[p]) == 1:
            link = dmc.NavLink(
                label=page['name'],
                href=page["relative_path"],
            )
            children[pages[p][0]] = link
        else:
            if pages[p][0] not in children:
                link = dmc.NavLink(
                    label=capitalise_each(pages[p][0]),
                    children=[],
                )
                children[pages[p][0]] = link
            link = dmc.NavLink(
                label=page['name'],
                href=page["relative_path"],
            )
            children[pages[p][0]].children.append(link)
    # Put groups in desired order. Adjust file name to sort individual pages within groups alphabetically
    menu = []
    order = [
        "recorders",
        "soundscape",
        "species",
        "weather",
        "settings",
    ]
    for group in order:
        menu.append(children[group])
    return dmc.ScrollArea(dmc.Stack(menu))
