import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
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
    FETCH_DATASET_CATEGORIES,
)
from utils import list2tuple

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
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("umap-filter-store", "data"),
)
def load_data(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    disclude_file_ids: List[str],
) -> str:
    # HACK: this should be available as debounce=True prop on the date-picker class
    # but dash mantine components hasn't supported this for some reason
    # rather than use a default value and double-compute, we'll just exit early
    if len(list(filter(None, dates))) < 2:
        return no_update
    files = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
    )
    return dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        sample_size=len(files),
        file_ids=frozenset(disclude_file_ids or []),
    ).to_json(
        date_format="iso",
        orient="table",
    )

@callback(
    Output("umap-category-orders", "data"),
    Input("dataset-select", "value"),
)
def load_categories(
    dataset_name: str,
) -> Dict[str, List[str]]:
    return dispatch(FETCH_DATASET_CATEGORIES, dataset_name=dataset_name)

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
    Input("umap-category-orders", "data"),
    Input("umap-sample-slider", "value"),
    Input("umap-opacity-slider", "value"),
    Input("umap-size-slider", "value"),
    Input("umap-colour-select", "value"),
    Input("umap-symbol-select", "value"),
    Input("umap-facet-row-select", "value"),
    Input("umap-facet-column-select", "value"),
    prevent_initial_call=True,
)
def draw_figure(
    json_data: str,
    category_orders: Dict[str, List[str]],
    sample_size: int,
    opacity: int,
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
) -> go.Figure:
    data = pd.read_json(StringIO(json_data), orient="table")

    fig = px.scatter(
        data.sample(min(len(data), sample_size)),
        x="UMAP Dim 1",
        y="UMAP Dim 2",
        opacity=opacity / 100.0,
        category_orders=category_orders,
        hover_name="file_id",
        hover_data=["file", "site", "dddn", "timestamp"],
        height=PLOT_HEIGHT,
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
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
