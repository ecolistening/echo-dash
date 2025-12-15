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
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES, DATASETS
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, send_download, safe_category_orders
from utils.sketch import default_layout

PLOT_HEIGHT = 400

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
        **kwargs,
    )
    fig.update_layout(
        title=dict(
            automargin=True,
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
        Output("times-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("times-size-slider", "value"),
        Input("times-opacity-slider", "value"),
        Input("times-colour-select", "value"),
        Input("times-symbol-select", "value"),
        Input("times-facet-row-select", "value"),
        Input("times-facet-column-select", "value"),
        Input("plotly-theme", "data"),
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
        template: str,
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
            hover_name="file_id",
            hover_data=[
                "file_name",
                "file_path",
                "timestamp",
                "site_name",
                "dddn",
                "hour_categorical",
                "week_of_year_categorical",
                "file_duration",
            ],
            labels={
                "file_name": "File Name",
                "file_path": "File Path",
                "timestamp": "Timestamp",
                "site_name": "Site",
                "dddn": "Dawn/Day/Dusk/Night",
                "hour_categorical": options.get("hour_categorical", {}).get("label", "hour_categorical"),
                "week_of_year_categorical": options.get("week_of_year_categorical", {}).get("label", "week_of_year_categorical"),
                "file_duration": "Duration (seconds)",
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
                symbol: options.get(symbol, {}).get("label", symbol),
            },
            category_orders=safe_category_orders(data, category_orders),
        )
        title_text = "Recording Times"
        fig.update_traces(marker=dict(size=dot_size))
        fig.update_layout(default_layout(fig))
        fig.update_layout(title_text=title_text)
        fig.update_layout(template=template)
        return fig

    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output({"type": "times-data-download-button", "index": MATCH}, "loading", allow_duplicate=True),
        Input({"type": "times-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output({"type": "times-data-download", "index": MATCH}, "data"),
        Output({"type": "times-data-download-button", "index": MATCH}, "loading"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        State({"type": "times-data-download-button", "index": MATCH}, "id"),
        Input({"type": "times-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        ids,
        clicks,
    ) -> Dict[str, Any]:
        if ids is None or not len(list(filter(None, ids))):
            return no_update
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        ), False
