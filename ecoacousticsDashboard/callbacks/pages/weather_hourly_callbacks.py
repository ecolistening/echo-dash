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

from api import dispatch, FETCH_DATASET_OPTIONS, FETCH_FILE_WEATHER
from utils import list2tuple, send_download

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_FILE_WEATHER,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(filters["files"].values()))),
    )

def plot(
    df: pd.DataFrame,
    variable: str,
    time_agg: str = "1W",
    color: str | None = None,
    facet_row: str | None = None,
    labels: Dict[str, str] | None = None,
    **kwargs: Any,
) -> go.Figure:
    df = (
        df[df.variable == variable]
        .drop_duplicates(["nearest_hour", "site_id"])
        .sort_values("nearest_hour")
        .groupby([*list(set(filter(None, [color, facet_row]))), pd.Grouper(key="nearest_hour", freq=time_agg)])
        .agg(value_mean=("value", "mean"), value_std=("value", "std"))
        .reset_index()
    )
    fig = px.line(
        data_frame=df,
        x="nearest_hour",
        y="value_mean",
        error_y="value_std",
        color=color,
        facet_row=facet_row,
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
        Output("weather-hourly-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("weather-hourly-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("weather-hourly-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("weather-hourly-variable-select", "value"),
        Input("weather-hourly-time-aggregation", "value"),
        Input("weather-hourly-colour-select", "value"),
        Input("weather-hourly-facet-row-select", "value"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        variable: str,
        time_agg: str,
        color: str,
        facet_row: str,
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = fetch_data(dataset_name, filters)
        fig = plot(
            data,
            variable=variable,
            time_agg=time_agg,
            color=color,
            facet_row=facet_row,
            labels=dict(nearest_hour="Time", value_mean="value"),
            category_orders=category_orders,
        )
        fig.update_layout(title_text=variable)
        return fig

    @callback(
        Output("weather-hourly-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "weather-hourly-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_weather",
            ctx.triggered_id["index"]
        )
