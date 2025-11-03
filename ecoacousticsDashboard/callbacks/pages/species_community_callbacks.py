import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import functools
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_BIRDNET_SPECIES
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils.figures.species_matrix import species_matrix as plot
from utils import list2tuple, send_download, safe_category_orders

def register_callbacks():
    @callback(
        Output("species-matrix-pagination-controls", "children"),
        State("dataset-select", "value"),
        Input("species-matrix-filter", "value"),
        Input("species-matrix-filter", "data"),
        prevent_initial_call=True,
    )
    def set_matrix_pagination(dataset_name: str, opt_group: str, select_data: List[str]):
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        opts = options.get(opt_group)
        if not opts:
            return []
        return [
            dmc.Text(
                children=opts["label"],
                size="sm",
                ta="right",
            ),
            dmc.SegmentedControl(
                id={"type": "species-matrix-group-control", "index": opt_group},
                persistence=True,
                value=opts["order"][0],
                data=[
                    {"label": name, "value": name}
                    for name in opts["order"]
                ],
            ),
        ]

    @callback(
        Output("species-community-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("species-threshold-slider", "value"),
        Input("species-community-axis-select", "value"),
        Input("species-community-facet-column-select", "value"),
        Input("species-matrix-filter", "value"),
        Input({"type": "species-matrix-group-control", "index": ALL}, "value"),
        Input("species-list-tickbox", "checked"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        threshold: float,
        axis_group: str,
        facet_col: str,
        opt_group: str,
        opts: str,
        species_checkbox: bool,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        action = FETCH_BIRDNET_SPECIES
        if not species_checkbox:
            filters["species"] = []
        payload = dict(dataset_name=dataset_name, threshold=threshold, **filter_dict_to_tuples(filters))
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        data = dispatch(action, **payload)
        if len(opts):
            data = data[data[opt_group] == opts[0]]
        fig = plot(data, axis_group, facet_col, None, safe_category_orders(data, category_orders))
        fig.update_layout(title_text=f"Species Matrix |{f' {opts[0]} |' if len(opts) else ''} p > {threshold}")
        return fig

    @callback(
        Output("species-community-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        State("species-threshold-slider", "value"),
        Input({"type": "species-community-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        threshold: float,
        clicks,
    ) -> Dict[str, Any]:
        action = FETCH_BIRDNET_SPECIES
        payload = dict(dataset_name=dataset_name, threshold=threshold, **filter_dict_to_tuples(filters))
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        data = dispatch(action, **payload)
        return send_download(
            data,
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        )
