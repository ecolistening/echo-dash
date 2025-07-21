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
    FETCH_ACOUSTIC_FEATURES,
    FETCH_DATASET_CATEGORIES,
)
from utils import list2tuple

PLOT_HEIGHT = 800

@callback(
    Output("distributions-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("distributions-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("distributions-graph-data", "data"),
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
    Output("distributions-graph", "figure"),
    Input("distributions-graph-data", "data"),
    Input("feature-dropdown", "value"),
    Input("distributions-colour-select", "value"),
    Input("distributions-facet-row-select", "value"),
    Input("distributions-facet-column-select", "value"),
    Input("distributions-normalised-tickbox", "checked"),
    Input("dataset-category-orders", "data"),
    prevent_initial_call=True,
)
def draw_figure(
    json_data: str,
    feature_name: str,
    color: str,
    facet_row: str,
    facet_col: str,
    normalised: bool,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    fig = px.histogram(
        data_frame=pd.read_json(
            StringIO(json_data),
            orient="table"
        ),
        x="value",
        marginal="rug",
        opacity=0.75,
        color=color,
        facet_row=facet_row,
        facet_col=facet_col,
        histnorm="percent" if normalised else None,
        labels=dict(
            value=feature_name.capitalize(),
        ),
        category_orders=category_orders,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=f"Soundscape Descriptor Distributions",
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    return fig
