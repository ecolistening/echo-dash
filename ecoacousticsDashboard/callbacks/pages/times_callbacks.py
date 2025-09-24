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
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES, DATASETS
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, send_download

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters, **kwargs):
    action = FETCH_FILES
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters), **kwargs)
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def plot(
    df: pd.DataFrame,
    opacity: int = 100,
    **kwargs: Any,
) -> go.Figure:
    fig = px.scatter(
        data_frame=df,
        x="date",
        y="time",
        opacity=opacity / 100,
        hover_name="file_id",
        hover_data=["file_name", "timestamp"],
        **kwargs,
    )
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            x=0.5,
            y=0.99,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        ),
        scattermode="group",
        scattergap=0.75,
    )
    return fig

def register_callbacks():
    @callback(
        Output("times-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("times-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("times-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("times-size-slider", "value"),
        Input("times-opacity-slider", "value"),
        Input("times-colour-select", "value"),
        Input("times-symbol-select", "value"),
        Input("times-facet-row-select", "value"),
        Input("times-facet-column-select", "value"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        dot_size: int,
        opacity: int,
        color: str,
        symbol: str,
        facet_row: str,
        facet_col: str,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters, valid_only=False)
        fig = plot(
            data,
            opacity=opacity,
            color=color,
            symbol=symbol,
            facet_row=facet_row,
            facet_col=facet_col,
            labels={
                "date": "Date",
                "time": "Hour",
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
                symbol: options.get(symbol, {}).get("label", symbol),
            },
            category_orders=category_orders,
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(title_text="Recording Times")
        fig.update_traces(marker=dict(size=dot_size))
        return fig

    @callback(
        Output("times-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "times-data-download-button", "index": ALL}, "n_clicks"),
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
