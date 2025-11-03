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
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, capitalise_each, send_download, safe_category_orders
from utils.sketch import default_layout

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("index-scatter-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("index-scatter-size-slider", "value"),
        Input("index-scatter-opacity-slider", "value"),
        Input("index-scatter-x-axis-select", "value"),
        Input("index-scatter-colour-select", "value"),
        Input("index-scatter-symbol-select", "value"),
        Input("index-scatter-facet-row-select", "value"),
        Input("index-scatter-facet-column-select", "value"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        dot_size: int,
        opacity: int,
        x_axis: str,
        color: str,
        symbol: str,
        facet_row: str,
        facet_col: str,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters)
        fig = px.scatter(
            data_frame=data,
            x=x_axis,
            y="value",
            hover_name="file_id",
            hover_data=["file_name", "file_path", "timestamp"],
            opacity=opacity / 100.0,
            color=color,
            symbol=symbol,
            facet_row=facet_row,
            facet_col=facet_col,
            color_discrete_sequence=px.colors.qualitative.Plotly,
            labels={
                "value": capitalise_each(filters["current_feature"]),
                x_axis: options.get(x_axis, {}).get("label", x_axis),
                color: options.get(color, {}).get("label", color),
                symbol: options.get(symbol, {}).get("label", symbol),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
            },
            category_orders=safe_category_orders(data, category_orders),
        )
        title_text = f"{capitalise_each(filters['current_feature'])} by Time of Day | {filters['date_range'][0]} - {filters['date_range'][1]}"
        fig.update_traces(marker=dict(size=dot_size))
        fig.update_layout(default_layout(fig, row_height=600))
        fig.update_layout(title_text=title_text)
        return fig

    @callback(
        Output("index-scatter-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "index-scatter-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_acoustic_indices",
            ctx.triggered_id["index"],
        )
