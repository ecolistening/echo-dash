import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import pandas as pd
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from plotly_calplot import calplot
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_FILES,
)
from components.figure_download_widget import FigureDownloadWidget
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

layout = html.Div([
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
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="dates-graph",
                        ),
                    ],
                ),
            ],
        ),
    ]),
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
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({'type': "checklist-locations-hierarchy", 'index': ALL}, 'value'),
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
) -> go.Figure:
    # HACK: this should be available as debounce=True prop on the date-picker class
    # but dash mantine components hasn't supported this for some reason
    if len(list(filter(lambda d: d is not None, dates))) < 2:
        return no_update
    triggered_id = ctx.triggered_id
    action = FETCH_FILES
    params = dict(
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations)
    )
    logger.debug(f"{triggered_id=} {action=} {params=}")
    data = dispatch(action, **params)
    data = data.groupby('date').agg('count').reset_index()
    fig = calplot(
        data,
        x='date',
        y='file'
    )
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig
