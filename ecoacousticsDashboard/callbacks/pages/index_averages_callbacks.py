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
from utils.figures.index_averages_scatter import plot
from utils import list2tuple, capitalise_each, send_download

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES
    payload = dict(dataset_name=dataset_name, filters=filters)
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("index-averages-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("index-averages-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("index-averages-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("index-averages-time-aggregation", "value"),
        Input("index-averages-colour-select", "value"),
        # Input(outliers_tickbox, "checked"),
        # Input(colours_tickbox, "checked"),
        # Input(separate_plots_tickbox, "checked"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        time_agg: str,
        color: str,
        # outliers,
        # colour_locations,
        # separate_plots,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters)
        fig = plot(
            data,
            time_agg,
            color=color,
            labels=dict(timestamp="Time", value_mean="value"),
            category_orders=category_orders,
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(title_text=f"{capitalise_each(filters['current_feature'])} Seasonal Averages")
        return fig

    @callback(
        Output("index-averages-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "index-averages-data-download-button", "index": ALL}, "n_clicks"),
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
