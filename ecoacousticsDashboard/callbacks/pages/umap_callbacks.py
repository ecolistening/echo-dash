import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES_UMAP
from utils import list2tuple, send_download

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(filters["files"].values()))),
    )

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
        hover_name="file_id",
        hover_data=["file_name", "site_name", "dddn", "timestamp"],
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        labels=labels,
        **kwargs,
    )
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
        Output("umap-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("umap-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(
        n_clicks: int,
        is_open: bool
    ) -> bool:
        return not is_open

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
        State("dataset-category-orders", "data"),
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
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = fetch_data(dataset_name, filters)
        fig = plot(
            data,
            opacity=opacity,
            color=color,
            symbol=symbol,
            facet_row=facet_row,
            facet_col=facet_col,
            labels=dict(x="UMAP Dim 1", y="UMAP Dim 2"),
            category_orders=category_orders,
        )
        fig.update_traces(marker=dict(size=dot_size))
        fig.update_layout(title_text="UMAP of Soundscape Descriptors")
        return fig

    @callback(
        Output("umap-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "umap-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_acoustic_features_umap",
            ctx.triggered_id["index"]
        )
