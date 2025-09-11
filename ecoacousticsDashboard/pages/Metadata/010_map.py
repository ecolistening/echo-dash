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
from components.figure_download_widget import FigureDownloadWidget
from components.footer import Footer
from utils import capitalise_each

PAGE_NAME = 'map'
PAGE_TITLE = 'Location Map'
PLOT_HEIGHT = 800

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
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="map-graph",
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(id="map-graph"),
    ),
    dmc.Space(h="sm"),
    dmc.Box(id="locations-table"),
    dbc.Offcanvas(
        id="map-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("map"),
    ),
])

from callbacks.pages import map_callbacks
