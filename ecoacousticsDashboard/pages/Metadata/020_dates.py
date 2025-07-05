import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from plotly_calplot import calplot
from typing import Any, Dict, List, Tuple

import components
from api import (
    dispatch,
    FETCH_FILES,
)
from utils import list2tuple

PAGE_NAME = 'dates'
PAGE_TITLE = 'Recording Dates'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Dates')

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
locations_hierarchy_id = "checklist-locations-hierarchy"
graph_id = f"{PAGE_NAME}-graph"

layout = html.Div([
    components.TopBar(
        dataset_id=dataset_select_id,
        graph_id=graph_id,
    ),
    dcc.Loading(
        dcc.Graph(id=graph_id),
    ),
    dbc.Offcanvas(
        id="page-info",
        is_open=False,
        placement="bottom",
        children=components.Footer(PAGE_NAME),
    ),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input({'type': locations_hierarchy_id, 'index': ALL}, 'value'),
)
def update_graph(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
) -> go.Figure:
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} dates:{len(dates)} locations:{len(locations)}")

    # FIXME: refactor into a unique API call
    data = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
    )
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
