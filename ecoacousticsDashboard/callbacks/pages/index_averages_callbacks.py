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
    Output("index-averages-graph-data", "data"),
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("umap-filter-store", "data"),
    Input("feature-dropdown", 'value'),
    Input("acoustic-feature-range-slider", "value"),
)
def load_data(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    file_filter_groups: Dict[int, List[str]],
    feature: str,
    feature_range: List[float],
) -> str:
    # HACK: this should be available as debounce=True prop on the date-picker class
    # but dash mantine components hasn't supported this for some reason
    # rather than use a default value and double-compute, we'll just exit early
    if len(list(filter(None, dates))) < 2:
        return no_update

    return dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
        feature=feature,
        # FIXME: hashing floating points will break the LRU cache
        # (1) set a fixed step-size and
        # (2) scale values and pass as integers along with scaling factor
        feature_range=list2tuple(feature_range),
    ).to_json(
        date_format="iso",
        orient="table",
    )

@callback(
    Output("index-averages-graph", "figure"),
    Input("index-averages-graph-data", "data"),
    Input("feature-dropdown", "value"),
    Input("index-averages-time-aggregation", "value"),
    # Input(outliers_tickbox, "checked"),
    # Input(colours_tickbox, "checked"),
    # Input(separate_plots_tickbox, "checked"),
    Input("dataset-category-orders", "data"),
    prevent_initial_call=True,
)
def draw_figure(
    json_data: str,
    feature_name: str,
    time_agg: str,
    # outliers,
    # colour_locations,
    # separate_plots,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    data = (
        pd.read_json(StringIO(json_data), orient="table")
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
            value_mean="</br></br>".join(map(str.capitalize, feature_name.split(" "))),
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
