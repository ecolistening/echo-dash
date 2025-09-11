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

from api import dispatch, FETCH_ACOUSTIC_FEATURES_UMAP
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
    Output("umap-graph", "figure"),
    State("dataset-select", "value"),
    Input("filter-store", "data"),
    # Input("umap-filter-store", "data"),
    Input("umap-opacity-slider", "value"),
    Input("umap-size-slider", "value"),
    Input("umap-colour-select", "value"),
    Input("umap-symbol-select", "value"),
    Input("umap-facet-row-select", "value"),
    Input("umap-facet-column-select", "value"),
    Input("dataset-category-orders", "data"),
)
def draw_figure(
    dataset_name: str,
    filters: Dict[str, Any],
    # file_filter_groups: Dict[int, List[str]],
    opacity: int,
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
        locations=list2tuple(filters["current_sites"]),
        # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )
    fig = px.scatter(
        data_frame=data,
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
    fig.update_traces(marker=dict(size=dot_size))
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text="UMAP of Soundscape Descriptors",
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig
