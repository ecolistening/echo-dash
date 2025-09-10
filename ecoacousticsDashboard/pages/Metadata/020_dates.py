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
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.footer import Footer
from utils import list2tuple

PAGE_NAME = 'dates'
PAGE_TITLE = 'Recording Dates'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Dates')

layout = dmc.Box([
    dcc.Store(id="dates-graph-data"),
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
                                    graph_data="dates-graph-data",
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
        dcc.Graph(id="dates-graph"),
    ),
    dbc.Offcanvas(
        id="dates-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("dates"),
    ),
])

@callback(
    Output("dates-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("dates-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("dates-graph", "figure"),
    State("dataset-select", "value"),
    Input("filter-store", "data"),
    # Input("umap-filter-store", "data"),
)
def draw_figure(
    dataset_name: str,
    filters: Dict[str, Any],
    # file_filter_groups: Dict[int, List[str]],
) -> go.Figure:
    data = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
        # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )
    data = (
        data
        .groupby("date")
        .agg("count")
        .reset_index()
    )
    fig = calplot(
        data,
        x="date",
        y="file_name"
    )
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            automargin=True,
            x=0.5,
            y=1.00,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        )
    )
    return fig
