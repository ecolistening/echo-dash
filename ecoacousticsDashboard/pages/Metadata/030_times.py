import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import itertools
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES, FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.figure_download_widget import FigureDownloadWidget
from components.footer import Footer
from utils import list2tuple
from utils.content import get_tabs

PAGE_NAME = 'times'
PAGE_TITLE = 'Recording Times'
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Times'
)

layout = dmc.Box([
    dcc.Store(id="times-graph-data"),
    FilterPanel([
        dmc.Group(
            align="start",
            grow=True,
            children=[
                SiteLevelFilter(),
                DateRangeFilter(),
                EnvironmentalFilter(),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="times-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="times-symbol-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="times-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="times-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet columns by"
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
                                    context="times",
                                ),
                                FigureDownloadWidget(
                                    plot_name="times-graph",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            grow=True,
            children=[
                dmc.Stack([
                    dmc.Text(
                        "Dot Size",
                        size="sm",
                        ta="left",
                    ),
                    dmc.Slider(
                        id="times-size-slider",
                        min=1,
                        max=20,
                        step=1,
                        value=4,
                        marks=[
                            {"value": i, "label": f"{i}"}
                            for i in (1, 10, 20)
                        ],
                        persistence=True
                    )
                ]),
                dmc.Stack([
                    dmc.Text(
                        "Opacity",
                        size='sm',
                        ta="left",
                    ),
                    dmc.Slider(
                        id="times-opacity-slider",
                        persistence=True,
                        min=0,
                        max=100,
                        step=5,
                        value=50,
                        marks=[
                            dict(value=i, label=f"{i}%")
                            for i in range(0, 101, 20)
                        ],
                    )
                ]),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(id="times-graph"),
    ),
    dbc.Offcanvas(
        id="times-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("times"),
    ),
    # TODO: fixme
    # get_modal_sound_sample(PAGE_NAME),
])

def register_callbacks():
    from callbacks.pages import times_callbacks
    times_callbacks.register_callbacks()
