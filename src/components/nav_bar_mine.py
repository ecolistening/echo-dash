import collections
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

NAVBAR_CONFIG = {
    "width": 300,
    "breakpoint": "sm",
    "collapsed": {
        "desktop": False,
        "mobile": True,
    },
}

def Menu():
    menu = []
    import code; code.interact(local=locals())
    groups = ["recorders", "soundscape", "species", "weather"]
    for group in groups:
        group_pages = {
            k: v for k, v in dash.page_registry.items()
            if k.startswith(f"pages.{group}")
        }
        if not len(group_pages):
            logger.warning(f"Can't find pages for '{group}'")
        elif len(group_pages) == 1:
            namespace, page_info = list(group_pages.items())[0]
            menu.append(dmc.NavLink(
                label=page_info["name"],
                href=page_info["path"],
            ))
        else:
            children = []
            for namespace, page_info in group_pages.items():
                children.append(dmc.NavLink(
                    label=page_info["name"],
                    href=page_info["path"],
                ))
            menu.append(dmc.NavLink(
                label=capitalise_each(group),
                children=children,
            ))
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
                # dmc.Box([
                #     dmc.Text("Active Filters", size="md"),
                #     dmc.Text(id="filter-state", size="sm", span=True),
                #     dmc.Space(h="sm"),
                #     dmc.Box(id="date-range-filter-chips"),
                #     dmc.Space(h="sm"),
                #     dmc.Box(id="acoustic-feature-range-filter-chips"),
                #     dmc.Space(h="sm"),
                #     dmc.Box(id="weather-variable-filter-chips"),
                #     dmc.Space(h="sm"),
                #     dmc.Box(id="file-filter-chips"),
                #     dmc.Space(h="sm"),
                #     dmc.Box(id="site-filter-chips"),
                # ])
            ]
        )
    )

