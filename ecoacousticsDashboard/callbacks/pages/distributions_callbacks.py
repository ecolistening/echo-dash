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
from api import filter_dict_to_tuples
from utils import list2tuple, capitalise_each, send_download, safe_category_orders
from utils.sketch import default_layout
from utils.figures.histogram import plot

PLOT_HEIGHT = 400

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
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
        data = fetch_data(dataset_name, filters)
        fig = plot(
            data,
            facet_row=facet_row,
            facet_col=facet_col,
            color=color,
            histnorm="percent" if normalised else None,
            category_orders=safe_category_orders(data, category_orders),
            labels={
                "count": "Count",
                "value": capitalise_each(filters["current_feature"]),
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
            },
        )
        fig.update_layout(default_layout(fig))
        fig.update_layout(title_text=f"{capitalise_each(filters['current_feature'])} | {filters['date_range'][0]} - {filters['date_range'][1]}")
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
