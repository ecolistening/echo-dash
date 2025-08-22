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

from api import (
    dispatch,
    FETCH_FILES,
    FETCH_ACOUSTIC_FEATURES_UMAP,
)
from utils import list2tuple, str2date

PLOT_HEIGHT = 800

@callback(
    Output("umap-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("umap-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(
    n_clicks: int,
    is_open: bool
) -> bool:
    return not is_open

@callback(
    Output("umap-graph-data", "data"),
    Input("dataset-select", "value"),
    Input("date-range-current-bounds", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "id"),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "value"),
    Input("umap-filter-store", "data"),
    prevent_initial_call=True,
)
def load_data(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    weather_variables: List[List[str]],
    weather_ranges: List[List[float]],
    file_filter_groups: Dict[int, List[str]],
) -> str:
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        sample_size=len(dispatch(FETCH_FILES, dataset_name=dataset_name)),
        file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
        **dict(zip(
            map(lambda match: match["index"], weather_variables),
            map(tuple, weather_ranges)
        )),
    )
    return data.to_json(
        date_format="iso",
        orient="table",
    )


@callback(
    Output("umap-sample-slider", "max"),
    Output("umap-sample-slider", "value"),
    Output("umap-sample-slider", "marks"),
    Input("umap-graph-data", "data"),
    prevent_initial_call=True,
)
def set_slider_range(
    json_data: str
) -> str:
    data = pd.read_json(StringIO(json_data), orient="table")
    max_samples = len(data)
    sample_size = max_samples
    mark_range = np.linspace(1, max_samples, 5, endpoint=True, dtype=int)
    marks = [dict(value=mark, label=f"{mark}") for mark in mark_range]
    return max_samples, sample_size, marks

@callback(
    Output("umap-graph", "figure"),
    Input("umap-graph-data", "data"),
    Input("umap-sample-slider", "value"),
    Input("umap-opacity-slider", "value"),
    Input("umap-size-slider", "value"),
    Input("umap-colour-select", "value"),
    Input("umap-symbol-select", "value"),
    Input("umap-facet-row-select", "value"),
    Input("umap-facet-column-select", "value"),
    Input("dataset-category-orders", "data"),
    prevent_initial_call=True,
)
def draw_figure(
    json_data: str,
    sample_size: int,
    opacity: int,
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    if json_data is None or not len(json_data):
        return no_update

    data = pd.read_json(
        StringIO(json_data),
        orient="table",
    )
    fig = px.scatter(
        data_frame=data.sample(min(len(data), sample_size)),
        x="x",
        y="y",
        opacity=opacity / 100.0,
        hover_name="file_id",
        hover_data=[
            "file_name",
            "site_name",
            "dddn",
            "timestamp"
        ],
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        labels=dict(
            x="UMAP Dim 1",
            y="UMAP Dim 2",
        ),
        category_orders=category_orders,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text="UMAP of Soundscape Descriptors",
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    fig.update_traces(
        marker=dict(size=dot_size)
    )

    return fig
