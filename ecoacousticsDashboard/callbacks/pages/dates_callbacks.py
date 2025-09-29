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
from api import filter_dict_to_tuples
from utils import list2tuple, send_download
from utils.figures.calendar import plot

def fetch_data(dataset_name, filters):
    action = FETCH_FILES
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("dates-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        data = fetch_data(dataset_name, filters)
        fig = plot(data)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
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
