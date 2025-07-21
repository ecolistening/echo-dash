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

NAVBAR_CONFIG = {
    "width": 300,
    "breakpoint": "sm",
    "collapsed": {
        "desktop": False,
        "mobile": True,
    },
}

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
                    label=pages[p][0],
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
    order = (
        'home',
        'Metadata',
        'Overview',
        'Diel',
        'Seasonal',
    )
    for group in order:
        menu.append(children[group])
    return dmc.Stack(menu)

def NavBar():
    return dmc.AppShellNavbar(
        id="navbar",
        p="md",
        w=NAVBAR_CONFIG["width"],
        children=dmc.ScrollArea(
            children=[
                Menu(),
                dmc.Space(h="1rem"),
                dmc.Divider(
                    variant="solid",
                    orientation="horizontal",
                ),
                dmc.Space(h="1rem"),
                dmc.Box([
                    dmc.Text("Active Filters", size="md"),
                    dmc.Text(id="filter-state", size="sm", span=True),
                    dmc.Space(h="sm"),
                    dmc.Box(id="date-range-filter-chips"),
                    dmc.Space(h="sm"),
                    dmc.Box(id="acoustic-feature-range-filter-chips"),
                    dmc.Space(h="sm"),
                    dmc.Box(id="file-filter-chips"),
                ])
            ]
        )
    )

