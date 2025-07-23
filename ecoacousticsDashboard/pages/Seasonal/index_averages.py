import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import dcc
from dash_iconify import DashIconify

from callbacks.pages import index_averages_callbacks
from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.figure_download_widget import FigureDownloadWidget
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.acoustic_feature_filter import AcousticFeatureFilter
from components.footer import Footer
from utils import list2tuple

PAGE_NAME = "idx-averages"
PAGE_TITLE = "Seasonal Descriptor Averages"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Averages"
)

windows_options = [
    { "description": "1 day", "frequency": "1D" },
    { "description": "1 week", "frequency": "1W" },
    { "description": "2 weeks", "frequency": "2W" },
    { "description": "1 month", "frequency": "1ME" },
    { "description": "3 months", "frequency": "3ME" },
    { "description": "6 months", "frequency": "6ME" },
]

layout = dmc.Box([
    dcc.Store(id="index-averages-graph-data"),
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
        dmc.Space(h=10),
        dmc.Group(
            align="start",
            grow=True,
            children=[
                AcousticFeatureFilter(),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                dmc.SegmentedControl(
                    id="index-averages-time-aggregation",
                    data=[
                        {"value": opt["frequency"], "label": opt["description"]}
                        for opt in windows_options
                    ],
                    value=windows_options[3]["frequency"],
                    persistence=True,
                ),
                # dmc.Chip(
                #     'Colour by Recorder',
                #     value='colour',
                #     checked=True,
                #     persistence=True,
                #     id='colour-locations'
                # ),
                # dmc.Chip(
                #     'Outliers',
                #     value='outlier',
                #     checked=True,
                #     persistence=True,
                #     id='outliers-tickbox'
                # ),
                # dmc.Chip(
                #     'Plot per Recorder',
                #     value='subplots',
                #     checked=False,
                #     persistence=True,
                #     id='separate-plots'
                # ),
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
                                    graph_data="index-averages-graph-data",
                                ),
                                FigureDownloadWidget(
                                    plot_name="index-averages-graph",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id="index-averages-graph"),
    ),
    dbc.Offcanvas(
        id="index-averages-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-averages"),
    ),
])
