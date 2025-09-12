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
from utils import list2tuple, capitalise_each, send_download
from utils.figures.histogram import plot

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        feature=filters["current_feature"],
        feature_range=list2tuple(filters["current_feature_range"]),
        **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(filters["files"].values()))),
    )

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
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        color: str,
        facet_row: str,
        facet_col: str,
        normalised: bool,
        category_orders: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        if not len(filters):
            return no_update
        fig = plot(
            fetch_data(dataset_name, filters),
            facet_row=facet_row,
            facet_col=facet_col,
            histnorm="percent" if normalised else None,
            labels=dict(value=capitalise_each(filters["current_feature"])),
            category_orders=category_orders,
        )
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
