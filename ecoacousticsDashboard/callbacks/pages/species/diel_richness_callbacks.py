import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import functools
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_BIRDNET_SPECIES
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, send_download, safe_category_orders
from utils import sketch
from utils.sketch import scatter_polar, default_layout

PLOT_HEIGHT = 800

def fetch_data(dataset_name, threshold, filters):
    action = FETCH_BIRDNET_SPECIES
    payload = dict(dataset_name=dataset_name, threshold=threshold, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def get_plot_type(plot_type: str):
    plot_type_mapping = {
        "Scatter": px.scatter,
        "Scatter Polar": sketch.scatter_polar,
    }
    assert plot_type in plot_type_mapping.keys(), f"'{plot_type}' is not a valid plot"
    return plot_type_mapping[plot_type]

def get_plot_params(plot_type: str, primary_axis: str, secondary_axis: str):
    plot_type_mapping = {
        "Scatter": dict(x=primary_axis, y=secondary_axis, **default_scatter_params()),
        "Scatter Polar": dict(theta=primary_axis, r=secondary_axis, **default_polar_params()),
    }
    assert plot_type in plot_type_mapping.keys(), f"'{plot_type}' is not a valid plot"
    return plot_type_mapping[plot_type]

def default_scatter_params():
    return dict()

def default_polar_params():
    return dict(
        mode="markers+lines",
        radialaxis=dict(
            showticklabels=True,
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=(angles := list(range(0, 360, 45))),
            ticktext=[f"{int(angle / 360 * 24)}" for angle in angles],
            direction="clockwise",
            rotation=90,
            ticks=""
        ),
    )

def register_callbacks():
    @callback(
        Output("species-richness-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("species-richness-plot-type-select", "value"),
        Input("species-richness-primary-axis-select", "value"),
        Input("species-threshold-slider", "value"),
        Input("species-richness-color-select", "value"),
        Input("species-richness-facet-row-select", "value"),
        Input("species-richness-facet-column-select", "value"),
        Input("species-list-tickbox", "checked"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        plot_type: str,
        primary_axis: str,
        threshold: str,
        color: str,
        facet_row: str,
        facet_col: str,
        species_checkbox: bool,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        if not species_checkbox:
            filters["species"] = []
        data = fetch_data(dataset_name, threshold, filters)
        data = (
            data
            .groupby(list(filter(None, set([primary_axis, "date", "hour_categorical", color, facet_row, facet_col]))))["species"]
            .nunique()
            .reset_index(name="richness")
        )
        data[primary_axis] = data[primary_axis] / 24
        plot = get_plot_type(plot_type)
        plot_params = get_plot_params(plot_type, primary_axis=primary_axis, secondary_axis="richness")
        fig = plot(
            data_frame=data,
            color=color,
            facet_row=facet_row,
            facet_col=facet_col,
            hover_data=["richness", primary_axis, "hour_categorical", color, facet_row, facet_col],
            labels={
                primary_axis: options.get(primary_axis, {}).get("label", primary_axis),
                "hour_categorical": options.get("hour_categorical", {}).get("label", "hour_categorical"),
                "richness": "Species Richness",
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
                facet_col: options.get(facet_col, {}).get("label", facet_col),
            },
            category_orders=safe_category_orders(data, category_orders),
            **plot_params,
        )
        fig.update_yaxes(rangemode="tozero")
        title_text = f"Species Richness by Time of Day | p > {threshold}"
        fig.update_layout(default_layout(fig, row_height=600))
        fig.update_layout(title_text=title_text, margin=dict(t=100))
        return fig

    @callback(
        Output("species-richness-data-download", "data"),
        State("dataset-select", "value"),
        Input("species-threshold-slider", "value"),
        State("filter-store", "data"),
        Input({"type": "species-richness-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        threshold: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, threshold, filters),
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        )

