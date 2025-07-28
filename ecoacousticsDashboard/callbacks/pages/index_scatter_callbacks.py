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
    Output("index-scatter-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("index-scatter-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("index-scatter-graph-data", "data"),
    Input("dataset-select", "value"),
    Input("date-range-current-bounds", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "id"),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "value"),
    Input("umap-filter-store", "data"),
    Input("acoustic-feature-current-bounds", "data"),
)
def load_data(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    weather_variables: List[List[str]],
    weather_ranges: List[List[float]],
    file_filter_groups: Dict[str, List],
    feature_params: Dict[str, Any],
) -> str:
    feature, start_value, end_value = feature_params.values()
    return dispatch(
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
    ).to_json(
        date_format="iso",
        orient="table",
    )

@callback(
    Output("index-scatter-graph", "figure"),
    Input("index-scatter-graph-data", "data"),
    Input("acoustic-feature-current-bounds", "data"),
    Input("index-scatter-size-slider", "value"),
    Input("index-scatter-colour-select", "value"),
    Input("index-scatter-symbol-select", "value"),
    Input("index-scatter-facet-row-select", "value"),
    Input("index-scatter-facet-column-select", "value"),
    Input("dataset-category-orders", "data"),
)
def draw_figure(
    json_data: str,
    feature_state: Dict[str, Any],
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    feature = feature_state["feature"]
    fig = px.scatter(
        data_frame=pd.read_json(
            StringIO(json_data),
            orient="table"
        ),
        x='hour',
        y='value',
        hover_name="file_id",
        hover_data=["file_name", "timestamp"],
        opacity=0.5,
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        labels=dict(
            hour="Hour",
            value=feature.capitalize(),
        ),
        category_orders=category_orders,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=f"Acoustic Descriptor by Time of Day",
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    fig.update_traces(marker=dict(size=dot_size))

    return fig
