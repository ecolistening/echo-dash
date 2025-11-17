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

dash.register_page(
    __name__,
    title="Settings",
    name="Settings",
)

def layout():
    return dmc.Box([
        dmc.Box([
            dmc.Title(id="settings-title", ta="center", size="xl", order=2),
        ]),
        dmc.Space(h="md"),
        dmc.Divider(variant="solid"),
        dmc.Space(h="md"),
        dmc.Box([
            dmc.Stack([
                dmc.Title('Site Hierarchy', ta="left", size="lg", order=3),
                dmc.Box(children=get_content("page/settings/site-hierarchy")),
                dmc.Space(h="sm"),
                dmc.Stack(
                    id="settings-sites-form",
                    children=[],
                ),
                dmc.Group(
                    grow=True,
                    children=[
                        dmc.Group(
                            justify="flex-end",
                            children=[
                                dmc.Button(
                                    "Save",
                                    id="settings-sites-save-button",
                                    variant="filled",
                                    color="green",
                                    leftSection=DashIconify(icon="fluent:save-28-filled"),
                                    n_clicks=0,
                                    mb=10,
                                ),
                            ]
                        )
                    ]
                )
            ]),
        ]),
        dmc.Space(h="md"),
        dmc.Divider(variant="solid"),
        dmc.Space(h="md"),
        dmc.Box([
            dmc.Title("Species List", ta="left", size="lg", order=3),
            dmc.Box(children=get_content("page/settings/species-list")),
            dmc.Space(h="sm"),
            ControlsPanel(
                is_open=True,
                children=[
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
                                        "Only Species List",
                                        id="species-list-tickbox",
                                        checked=False,
                                    ),
                                ]),
                                dmc.Group(
                                    justify="flex-end",
                                    children=[
                                        dmc.Button(
                                            "Save",
                                            id="species-list-save-button",
                                            leftSection=DashIconify(icon="fluent:save-28-filled"),
                                            color="green",
                                            size="sm",
                                        ),
                                        dmc.Button(
                                            "Reset",
                                            id="species-list-clear-button",
                                            leftSection=DashIconify(icon="material-symbols:cancel"),
                                            color="red",
                                            size="sm",
                                        ),
                                    ]
                                ),
                            ]),
                        ]
                    ),
                ]
            ),
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
        ])
    ])

def register_callbacks():
    from callbacks.pages import settings_callbacks
    settings_callbacks.register_callbacks()
