import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import string

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from components.controls_panel import ControlsPanel
from components.data_download_widget import DataDownloadWidget
from utils import capitalise_each
from utils.content import get_content

PAGE_NAME = 'species-list'
PAGE_TITLE = 'Species List'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Species List'
)

# TODO: add a button to show selected only

layout = html.Div([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                dmc.Stack([
                    dmc.Group([
                        dmc.TextInput(
                            id="species-search",
                            label="Search...",
                            value="",
                            leftSection=DashIconify(icon="cil:search"),
                            w=300,
                        ),
                        dmc.Select(
                            id="species-name-select",
                            label="Sort by",
                            value="scientific_name",
                            data=[
                                dict(value="scientific_name", label="Scientific Name"),
                                dict(value="common_name", label="Common Name"),
                            ],
                            clearable=False,
                            allowDeselect=False,
                            persistence=True,
                            w=300,
                        ),
                        dmc.Chip(
                            "Group Alphabetically",
                            id="alphabetic-tickbox",
                            persistence=True,
                            checked=True,
                        ),
                        dmc.Chip(
                            "Show Species List",
                            id="species-list-tickbox",
                            style={"display": "none"},
                            persistence=True,
                            checked=False,
                        ),
                    ]),
                    dmc.Group(
                        justify="flex-end",
                        children=[
                            dmc.Button(
                                "Save",
                                id="species-list-save-button",
                                color="green",
                                size="sm",
                            ),
                            dmc.Button(
                                "Reset",
                                id="species-list-clear-button",
                                color="red",
                                size="sm",
                            ),
                        ]
                    ),
                ]),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    dmc.Stack([
        dmc.SegmentedControl(
            id="species-pagination",
            value="A",
            data=[
                dict(label=l, value=l)
                for l in list(string.ascii_uppercase)
            ],
            fullWidth=True,
        ),
        dmc.Stack(
            id="species-table",
            style={"display": "block"},
            children=[
                dmc.Group(
                    justify="center",
                    children=[
                        dmc.Pagination(
                            id="species-table-pagination",
                            total=1,
                            value=1,
                            siblings=1,
                            boundaries=1
                        ),
                    ]
                ),
                dmc.Space(h="sm"),
                dmc.Grid(
                    id="species-table-checklist",
                    gutter="md",
                ),
            ]
        ),
        dmc.Stack(
            id="species-list-table",
            style={"display": "none"},
            children=[
                dmc.Group(
                    justify="center",
                    children=[
                        dmc.Pagination(
                            id="species-list-pagination",
                            total=1,
                            value=1,
                            siblings=1,
                            boundaries=1
                        ),
                    ]
                ),
                dmc.Space(h="sm"),
                dmc.Grid(
                    id="species-list-checklist",
                    gutter="md",
                ),
            ],
        )
    ]),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/species-list")
    ),
])

def register_callbacks():
    from callbacks.pages import species_list_callbacks
    species_list_callbacks.register_callbacks()
