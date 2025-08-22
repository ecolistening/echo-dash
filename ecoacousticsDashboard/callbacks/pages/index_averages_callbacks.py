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
from utils import list2tuple

PLOT_HEIGHT = 800

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
    Input("dataset-select", "value"),
    Input("date-range-current-bounds", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "id"),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "value"),
    Input("umap-filter-store", "data"),
    Input("acoustic-feature-current-bounds", "data"),
    Input("index-averages-time-aggregation", "value"),
    # Input(outliers_tickbox, "checked"),
    # Input(colours_tickbox, "checked"),
    # Input(separate_plots_tickbox, "checked"),
    Input("dataset-category-orders", "data"),
    prevent_initial_call=True,
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    weather_variables: List[List[str]],
    weather_ranges: List[List[float]],
    file_filter_groups: Dict[str, List],
    feature_params: Dict[str, Any],
    time_agg: str,
    # outliers,
    # colour_locations,
    # separate_plots,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    feature, start_value, end_value = feature_params.values()
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
        **dict(zip(
            map(lambda match: match["index"], weather_variables),
            map(tuple, weather_ranges)
        )),
        feature=feature,
        feature_range=(start_value, end_value),
    )
    data = (
        data
        .sort_values("timestamp")
        .groupby(by=[
            "location",
            "recorder",
            "feature",
            "dddn",
            pd.Grouper(key="timestamp", freq=time_agg)
        ])
        .agg({"value": ["mean", "std"]})
        .reset_index()
    )
    data.columns = [
        "_".join(filter(None, col_levels))
        for col_levels in data.columns.to_flat_index()
    ]
    fig = px.line(
        data_frame=data,
        x="timestamp",
        y="value_mean",
        error_y="value_std",
        color="location",
        facet_row="dddn",
        markers=True,
        labels=dict(
            timestamp="Time",
            value_mean="</br></br>".join(map(str.capitalize, feature.split(" "))),
        ),
        category_orders=category_orders,
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text="Seasonal Descriptor Averages",
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig
