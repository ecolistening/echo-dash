import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import dcc
from dash_iconify import DashIconify

from api import FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.figure_download_widget import FigureDownloadWidget
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from utils import list2tuple, send_download
from utils.content import get_content
from utils.sketch import empty_figure

dash.register_page(
    __name__,
    title="Soundscape Descriptor Seasonal Averages",
    name="Seasonal Averages",
    path="/soundscape/seasonal-averages",
    order=1,
)

layout = dmc.Box([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                dmc.Select(
                    id="feature-select",
                    label="Acoustic Feature",
                    value="bioacoustic index",
                    searchable=True,
                    clearable=False,
                    allowDeselect=False,
                ),
                DatasetOptionsSelect(
                    id="index-averages-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level",),
                    label="Colour by",
                    value="sitelevel_1",
                ),
                dmc.Chip(
                    id="index-averages-year-wrap-checkbox",
                    children="Annual Wrap",
                    checked=False,
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
                                    context="index-averages",
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
        dmc.Group(
            grow=True,
            children=[
                dmc.Stack([
                    dmc.Text(
                        "Acoustic Feature Range",
                        id="feature-range-title",
                        size="sm",
                        ta="left",
                    ),
                    dmc.RangeSlider(
                        id="feature-range-slider",
                        min=0,
                        max=999,
                        step=1,
                        persistence=True,
                        showLabelOnHover=False,
                    ),
                ]),
                dmc.Stack([
                    dmc.Text(
                        "Time Aggregation",
                        size="sm",
                        ta="left",
                    ),
                    dmc.SegmentedControl(
                        id="index-averages-time-aggregation",
                        data=[
                            {"label": "1 day", "value": "1D"},
                            {"label": "1 week", "value": "1W"},
                            {"label": "2 weeks", "value": "2W"},
                            {"label": "1 month", "value": "1ME"},
                            {"label": "3 months", "value": "3ME"},
                            {"label": "6 months", "value": "6ME"},
                        ],
                        value="1W",
                        persistence=True,
                    ),
                ]),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(
            id="index-averages-graph",
            figure=empty_figure("Loading data..."),
        ),
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/acoustic-feature-seasonal-averages")
    ),
    dmc.Box(
        id="soundade-features-description",
        children=[]
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="feature-descriptor-content",
        children=[],
    ),
])

def register_callbacks():
    from callbacks.pages.soundscape import seasonal_averages_callbacks
    seasonal_averages_callbacks.register_callbacks()
