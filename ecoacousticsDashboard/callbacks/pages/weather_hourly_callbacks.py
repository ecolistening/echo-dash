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

from api import dispatch, FETCH_FILE_WEATHER
from utils import list2tuple

PLOT_HEIGHT = 800

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
    Input("dataset-select", "value"),
    Input("filter-store", "data"),
    # Input("umap-filter-store", "data"),
    Input("weather-hourly-variable-select", "value"),
    Input("weather-hourly-time-aggregation", "value"),
    Input("weather-hourly-colour-select", "value"),
    Input("weather-hourly-facet-row-select", "value"),
    Input("dataset-category-orders", "data"),
)
def draw_figure(
    dataset_name: str,
    filters: Dict[str, Any],
    # file_filter_groups: Dict[int, List[str]],
    variable: str,
    time_agg: str,
    color: str,
    facet_row: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    data = dispatch(
        FETCH_FILE_WEATHER,
        dataset_name=dataset_name,
        variable=variable,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )
    if not len(data):
        return {}
    data = (
        data
        .drop_duplicates(["timestamp_weather", "site_id"])
        .sort_values("timestamp_weather")
        .groupby([*list(set(filter(None, [color, facet_row]))), pd.Grouper(key="timestamp_weather", freq=time_agg)])
        .agg(value_mean=("value", "mean"), value_std=("value", "std"))
        .reset_index()
    )
    fig = px.line(
        data_frame=data_frame,
        x="timestamp_weather",
        y="value_mean",
        error_y="value_std",
        color=color,
        facet_row=facet_row,
        markers=True,
        labels=dict(
            timestamp_weather="Time",
            value_mean="value",
        ),
        category_orders=category_orders,
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=variable,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig
