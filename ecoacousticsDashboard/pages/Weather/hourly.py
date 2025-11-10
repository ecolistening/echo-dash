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
from utils import list2tuple
from utils.content import get_content

PAGE_NAME = "weather-hourly"
PAGE_TITLE = "Hourly Weather"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Averages"
)

layout = dmc.Box([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="weather-hourly-variable-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Temperature", "Precipitation", "Wind"),
                    label="Weather Variable",
                    value="temperature_2m",
                    clearable=False,
                    allowDeselect=False,
                ),
                DatasetOptionsSelect(
                    id="weather-hourly-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level",),
                    label="Colour by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="weather-hourly-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level",),
                    label="Facet rows by",
                    value="sitelevel_1",
                ),
                dmc.Chip(
                    id="weather-hourly-year-wrap-checkbox",
                    children="Annual Wrap",
                    checked=False,
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
                                    context="weather-hourly",
                                ),
                                FigureDownloadWidget(
                                    plot_name="weather-hourly-graph",
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
                        "Time Aggregation",
                        size="sm",
                        ta="left",
                    ),
                    dmc.SegmentedControl(
                        id="weather-hourly-time-aggregation",
                        data=[
                            {"label": "1 hour", "value": "1h"},
                            {"label": "6 hours", "value": "6h"},
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
        dcc.Graph(id="weather-hourly-graph"),
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/weather-hourly")
    ),
])

def register_callbacks():
    from callbacks.pages import weather_hourly_callbacks
    weather_hourly_callbacks.register_callbacks()
