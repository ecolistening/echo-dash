import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

import components
from api import dispatch, FETCH_LOCATIONS
from utils.content import get_tabs
from utils.save_plot_fig import get_save_plot

PAGE_NAME = 'map'
PAGE_TITLE = 'Location Map'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Map')

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
graph_id = f"{PAGE_NAME}-graph"

layout = html.Div([
    components.TopBar(
        dataset_id=dataset_select_id,
        graph_id=graph_id,
    ),
    dmc.Divider(variant='dotted'),
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
)
def update_graph(dataset_name):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=}")

    data = dispatch(
        FETCH_LOCATIONS,
        dataset_name=dataset_name,
    )
    '''
        Calculate Zoom Level for World Map

        https://docs.mapbox.com/help/glossary/zoom-level/#zoom-levels-and-geographical-distance
    '''
    extents = data.describe()
    longitude_range = extents.loc['max', 'longitude'] - extents.loc['min', 'longitude']
    latitude_range = extents.loc['max', 'latitude'] - extents.loc['min', 'latitude']

    # The 111 is a constant to convert decimal degrees to kilometers
    max_bound = max(longitude_range, latitude_range) * 111

    # Formula established by trial-and-error
    zoom = 12 - np.log(max_bound)*1.1

    logger.debug(f"{dataset_name=} {latitude_range=:.4f} {longitude_range=:.4f} {max_bound=:.4f} {np.log(max_bound)=:.4f} {zoom=:.4f}")

    fig = px.scatter_mapbox(
        data,
        lat="latitude",
        lon="longitude",
        hover_name="site",
        hover_data=['timezone'],
        color_discrete_sequence=["red"],
        zoom=zoom,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style="open-street-map",
    )

    return fig
