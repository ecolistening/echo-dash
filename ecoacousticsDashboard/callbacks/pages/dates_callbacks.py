import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import itertools
import numpy as np
import pandas as pd

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES
from utils import list2tuple, send_download
from utils.figures.calendar import plot

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
        # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )

def register_callbacks():
    @callback(
        Output("dates-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("dates-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("dates-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        # file_filter_groups: Dict[int, List[str]],
    ) -> Dict[str, Any]:
        data = fetch_data(dataset_name, filters)
        fig = plot(data)
        fig.update_layout(title_text="Recording Dates")
        return fig

    @callback(
        Output("dates-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "dates-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_dates",
            ctx.triggered_id["index"]
        )
