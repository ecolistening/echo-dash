import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_LOCATIONS
from components.controls_panel import ControlsPanel
from components.data_download_widget import DataDownloadWidget
from components.figure_download_widget import FigureDownloadWidget
from utils import capitalise_each
from utils.content import get_content

PAGE_NAME = 'map'
PAGE_TITLE = 'Location Map'
PLOT_HEIGHT = 400

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Map'
)

layout = html.Div([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                dmc.Select(
                    id="map-style-select",
                    label="Map Style",
                    value="satellite",
                    persistence=True,
                    data=[
                        {"value": "satellite-streets", "label": "Satellite Streets"},
                        {"value": "satellite", "label": "Satellite"},
                        {"value": "open-street-map", "label": "Open Street Map"},
                        {"value": "outdoors", "label": "Outdoors"},
                    ]
                ),
                dmc.Flex(
                    p="1rem",
                    align="center",
                    justify="right",
                    direction="row",
                    children=[
                        dmc.Group(
                            grow=True,
                            children=[
                                DataDownloadWidget(
                                    context="map",
                                ),
                                FigureDownloadWidget(
                                    plot_name="map-graph",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(
            id="map-graph",
            # responsive=True,
        ),
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/map")
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="locations-paginated-table",
        children=dmc.Stack([
            dmc.Group([
                dmc.TextInput(
                    id="locations-search",
                    placeholder="Search...",
                    value="",
                    leftSection=DashIconify(icon="cil:search"),
                    w=300,
                ),
                dmc.Pagination(
                    id="locations-paginated",
                    total=1,
                    value=1,
                    siblings=1,
                    boundaries=1,
                ),
            ]),
            dmc.Box(
                id="locations-table-container",
                children=[]
            ),
        ])
    ),
])

def register_callbacks():
    from callbacks.pages import map_callbacks
    map_callbacks.register_callbacks()
