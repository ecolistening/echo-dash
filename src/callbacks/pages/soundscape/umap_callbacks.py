import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update, clientside_callback
from dash import Output, Input, State, ALL, MATCH
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES_UMAP
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, send_download
from utils.sketch import default_layout

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES_UMAP
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def plot(
    df: pd.DataFrame,
    opacity: int = 100,
    color: str | None = None,
    symbol: str | None = None,
    facet_row: str | None = None,
    facet_col: str | None = None,
    labels: Dict[str, str] | None = None,
    **kwargs: Any,
) -> go.Figure:
    fig = px.scatter(
        data_frame=df,
        x="x",
        y="y",
        opacity=opacity / 100.0,
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        labels=labels,
        **kwargs,
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig

def register_callbacks():
    @callback(
        Output("umap-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("umap-opacity-slider", "value"),
        Input("umap-size-slider", "value"),
        Input("umap-colour-select", "value"),
        Input("umap-symbol-select", "value"),
        Input("umap-facet-row-select", "value"),
        Input("umap-facet-column-select", "value"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        opacity: int,
        dot_size: int,
        color: str,
        symbol: str,
        facet_row: str,
        facet_col: str,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters)
        fig = plot(
            data,
            opacity=opacity,
            color=color,
            symbol=symbol,
            facet_row=facet_row,
            facet_col=facet_col,
            hover_name="file_id",
            hover_data=[
                "file_name",
                "file_path",
                "timestamp",
                "site_name",
                "dddn",
                "hour_categorical",
                "week_of_year_categorical",
                "duration",
                "offset",
            ],
            labels={
                "x": "UMAP Dim 1",
                "y": "UMAP Dim 2",
                "file_name": "File Name",
                "file_path": "File Path",
                "timestamp": "Timestamp",
                "site_name": "Site",
                "dddn": "Dawn/Day/Dusk/Night",
                "hour_categorical": options.get("hour_categorical", {}).get("label", "hour_categorical"),
                "week_of_year_categorical": options.get("week_of_year_categorical", {}).get("label", "week_of_year_categorical"),
                "duration": "Duration (seconds)",
                "offset": "Start Time (seconds)",
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
                symbol: options.get(symbol, {}).get("label", symbol),
            },
            category_orders=category_orders,
        )
        fig.update_traces(marker=dict(size=dot_size))
        fig.update_layout(default_layout(fig, row_height=800))
        fig.update_layout(title_text="UMAP of Soundscape Descriptors")
        return fig

    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output({"type": "umap-data-download-button", "index": MATCH}, "loading", allow_duplicate=True),
        Input({"type": "umap-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output({"type": "umap-data-download", "index": MATCH}, "data"),
        Output({"type": "umap-data-download-button", "index": MATCH}, "loading"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "umap-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        n_clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_acoustic_features_umap",
            ctx.triggered_id["index"]
        ), False
