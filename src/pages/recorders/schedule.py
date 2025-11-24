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
from components.file_selection_sidebar import FileSelectionSidebar, FileSelectionSidebarIcon
from utils import list2tuple
from utils.content import get_content
from utils.sketch import empty_figure

dash.register_page(
    __name__,
    title="Recording Schedule",
    name="Schedule",
    path="/recorders/schedule",
    order=2,
)

layout = dmc.Box([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="times-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("File Level", "Site Level", "Time of Day", "Temporal"), #, "Spatial"),
                    label="Colour by",
                    value="valid",
                ),
                DatasetOptionsSelect(
                    id="times-symbol-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("File Level", "Site Level", "Time of Day", "Temporal"), #, "Spatial"),
                    label="Symbol by",
                ),
                DatasetOptionsSelect(
                    id="times-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("File Level", "Site Level", "Time of Day", "Temporal"), #, "Spatial"),
                    label="Facet rows by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="times-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("File Level", "Site Level", "Time of Day", "Temporal"), #, "Spatial"),
                    label="Facet columns by",
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
                                FileSelectionSidebarIcon(context="times"),
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
    dmc.Grid([
        dmc.GridCol(
            id="times-graph-container",
            span=12,
            children=[
                dcc.Loading([
                    dcc.Graph(
                        id="times-graph",
                        figure=empty_figure("Loading data..."),
                        # responsive=True,
                    ),
                ]),
            ],
        ),
        FileSelectionSidebar(
            context="times",
            graph="times-graph",
            sibling="times-graph-container",
            span=5,
        ),
    ]),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/times")
    ),
])

def register_callbacks():
    from callbacks.pages.recorders import schedule_callbacks
    schedule_callbacks.register_callbacks()
