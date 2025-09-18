import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import itertools
import numpy as np
import pandas as pd

from dash import html, dcc, callback, ctx, no_update, clientside_callback
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from utils import list2tuple, capitalise_each, send_download
from utils.figures.histogram import plot

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES
    payload = dict(dataset_name=dataset_name, filters=filters)
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("distributions-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("distributions-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("distributions-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("distributions-colour-select", "value"),
        Input("distributions-facet-row-select", "value"),
        Input("distributions-facet-column-select", "value"),
        Input("distributions-normalised-tickbox", "checked"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        color: str,
        facet_row: str,
        facet_col: str,
        normalised: bool,
    ) -> Dict[str, Any]:
        if not len(filters):
            return no_update
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        fig = plot(
            fetch_data(dataset_name, filters),
            facet_row=facet_row,
            facet_col=facet_col,
            color=color,
            histnorm="percent" if normalised else None,
            # labels=dict(value=capitalise_each(filters["current_feature"])),
            category_orders=category_orders,
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(title_text=(
            f"{capitalise_each(filters['current_feature'])} | "
            f"{filters['date_range'][0]} - {filters['date_range'][1]}"
        ))
        return fig

    @callback(
        Output("distributions-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "distributions-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_acoustic_features",
            ctx.triggered_id["index"]
        )
