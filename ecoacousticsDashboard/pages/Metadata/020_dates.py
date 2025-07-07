import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
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
from components.top_bar import TopBar
from components.footer import Footer
from utils import list2tuple

PAGE_NAME = 'dates'
PAGE_TITLE = 'Recording Dates'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Dates')

layout = html.Div([
    TopBar("dates"),
    dcc.Loading(
        dcc.Graph(id=f"dates-graph"),
    ),
    dbc.Offcanvas(
        id="page-info",
        is_open=False,
        placement="bottom",
        children=Footer("dates"),
    ),
])

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
