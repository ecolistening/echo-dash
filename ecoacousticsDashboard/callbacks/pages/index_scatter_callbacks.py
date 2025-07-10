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
    disclude_file_ids: List[str],
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
        file_ids=frozenset(disclude_file_ids or []),
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
    Output("index-scatter-graph", "figure"),
    Input("index-scatter-graph-data", "data"),
    Input("feature-dropdown", "value"),
    Input("index-scatter-size-slider", "value"),
    Input("index-scatter-colour-select", "value"),
    Input("index-scatter-symbol-select", "value"),
    Input("index-scatter-facet-row-select", "value"),
    Input("index-scatter-facet-column-select", "value"),
    Input("dataset-category-orders", "data"),
)
def draw_figure(
    json_data: str,
    feature_name: str,
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
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
            value=feature_name.capitalize(),
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
