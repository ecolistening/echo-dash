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
from components.footer import Footer
from utils import list2tuple

PAGE_NAME = "weather-hourly"
PAGE_TITLE = "Hourly Weather"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Averages"
)

windows_options = [
    { "description": "1 hour", "frequency": "1h" },
    { "description": "6 hours", "frequency": "6h" },
    { "description": "1 day", "frequency": "1D" },
    { "description": "1 week", "frequency": "1W" },
    { "description": "2 weeks", "frequency": "2W" },
    { "description": "1 month", "frequency": "1ME" },
    { "description": "3 months", "frequency": "3ME" },
    { "description": "6 months", "frequency": "6ME" },
]

layout = dmc.Box([
    dcc.Store(id="weather-hourly-graph-data"),
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
                    value="location",
                ),
                DatasetOptionsSelect(
                    id="weather-hourly-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level",),
                    label="Facet rows by",
                    value="location",
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
                            {"value": opt["frequency"], "label": opt["description"]}
                            for opt in windows_options
                        ],
                        value=windows_options[3]["frequency"],
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
    dbc.Offcanvas(
        id="weather-hourly-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("weather-hourly"),
    ),
])

def register_callbacks():
    from callbacks.pages import weather_hourly_callbacks
    weather_hourly_callbacks.register_callbacks()
