import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import itertools
import pandas as pd
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from plotly_calplot import calplot
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES
from components.figure_download_widget import FigureDownloadWidget
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from utils import list2tuple
from utils.content import get_content
from utils.sketch import empty_figure

dash.register_page(
    __name__,
    title="Recording Calendar",
    name="Calendar",
    path="/recorders/calendar",
    order=1,
)

layout = dmc.Box([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
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
                                    context="dates",
                                ),
                                FigureDownloadWidget(
                                    plot_name="dates-graph",
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
            id="dates-graph",
            figure=empty_figure("Loading data..."),
            # responsive=True,
        ),
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/dates")
    ),
])

def register_callbacks():
    from callbacks.pages.recorders import calendar_callbacks
    calendar_callbacks.register_callbacks()
