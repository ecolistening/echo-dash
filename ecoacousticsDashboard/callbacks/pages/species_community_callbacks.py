import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import functools
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_BIRDNET_SPECIES
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from utils.figures.species_matrix import species_matrix as plot
from utils import list2tuple, send_download

def register_callbacks():
    @callback(
        Output("species-community-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("species-community-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("species-community-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("species-threshold-slider", "value"),
        Input("species-community-axis-select", "value"),
        Input("species-community-facet-column-select", "value"),
        Input("species-community-facet-row-select", "value"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        threshold: float,
        axis_group: str,
        facet_col: str,
        facet_row: str,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        action = FETCH_BIRDNET_SPECIES
        payload = dict(dataset_name=dataset_name, threshold=threshold, filters=filters)
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        data = dispatch(action, **payload)
        fig = plot(data, axis_group, facet_col, facet_row, category_orders)
        fig.update_layout(title_text=f"Species Matrix | p > {threshold}")
        return fig

    @callback(
        Output("species-community-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        State("species-threshold-slider", "value"),
        Input({"type": "species-community-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        threshold: float,
        clicks,
    ) -> Dict[str, Any]:
        action = FETCH_BIRDNET_SPECIES
        payload = dict(dataset_name=dataset_name, threshold=threshold, filters=filters)
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        data = dispatch(action, **payload)
        return send_download(
            data,
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        )
