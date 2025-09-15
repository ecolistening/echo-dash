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
from utils.figures.species_matrix import species_matrix as plot
from utils import list2tuple, send_download

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_BIRDNET_SPECIES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(filters["files"].values()))),
    )

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
        Input("species-community-threshold-slider", "value"),
        Input("species-community-axis-select", "value"),
        Input("species-community-facet-column-select", "value"),
        Input("species-community-facet-row-select", "value"),
        State("dataset-options", "data"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        threshold: float,
        axis_group: str,
        facet_col: str,
        facet_row: str,
        options: Dict[str, List[str]],
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = fetch_data(dataset_name, filters)
        data["detected"] = (data["confidence"] > threshold).astype(int)
        fig = plot(data, axis_group, facet_col, facet_row, category_orders)
        fig.update_layout(title_text=f"Species Matrix | p > {threshold}")
        return fig

    @callback(
        Output("species-community-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "species-community-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        )
