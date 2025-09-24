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
from utils import list2tuple, capitalise_each, send_download

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES
    payload = dict(dataset_name=dataset_name, filters=filters)
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("index-box-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("index-box-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("index-box-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("index-box-time-aggregation", "value"),
        Input("index-box-outliers-tickbox", "checked"),
        Input("index-box-colour-select", "value"),
        Input("index-box-facet-row-select", "value"),
        Input("index-box-facet-column-select", "value"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        time_agg: str,
        outliers: bool,
        color: str,
        facet_row: str,
        facet_col: str,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters)
        fig = px.box(
            data_frame=data,
            x=time_agg,
            y="value",
            hover_name="file_id",
            hover_data=["file_name", "timestamp"],
            color=color,
            facet_row=facet_row,
            facet_col=facet_col,
            # facet_col_wrap=4,
            labels={
                "value": capitalise_each(filters["current_feature"]),
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
            },
            points="outliers" if outliers else False,
            category_orders=category_orders,
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(
            height=PLOT_HEIGHT,
            margin=dict(t=80),
            title=dict(
                text=f"Box Plot of Acoustic Descriptor by Time of Day",
                x=0.5,
                y=0.98,
                font=dict(size=24),
            )
        )
        return fig

    @callback(
        Output("index-box-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "index-box-data-download-button", "index": ALL}, "n_clicks"),
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
