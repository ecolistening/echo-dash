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
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES
from utils import list2tuple, capitalise_each, send_download

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
        # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )

def plot(
    df: pd.DataFrame,
    time_agg: str = "1W",
    color: str | None = None,
    labels: Dict[str, str] | None = None,
    **kwargs: Any,
) -> go.Figure:
    df = (
        df.sort_values("timestamp")
        .groupby(list(filter(None, [color, "feature", "dddn", pd.Grouper(key="timestamp", freq=time_agg)])))
        .agg({"value": ["mean", "std"]})
        .reset_index()
    )
    df.columns = ["_".join(filter(None, col_levels)) for col_levels in df.columns.to_flat_index()]
    fig = px.line(
        data_frame=df,
        x="timestamp",
        y="value_mean",
        error_y="value_std",
        color=color,
        facet_row="dddn",
        markers=True,
        labels=labels,
        **kwargs,
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig

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
        # Input("umap-filter-store", "data"),
        Input("index-averages-time-aggregation", "value"),
        Input("index-averages-colour-select", "value"),
        # Input(outliers_tickbox, "checked"),
        # Input(colours_tickbox, "checked"),
        # Input(separate_plots_tickbox, "checked"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        # file_filter_groups: Dict[str, List],
        time_agg: str,
        color: str,
        # outliers,
        # colour_locations,
        # separate_plots,
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = fetch_data(dataset_name, filters)
        fig = plot(
            data,
            time_agg,
            color=color,
            labels=dict(timestamp="Time", value_mean=capitalise_each(filters["current_feature"])),
            category_orders=category_orders,
        )
        fig.update_layout(title_text="Seasonal Descriptor Averages")
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
