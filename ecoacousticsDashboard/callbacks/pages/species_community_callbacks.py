import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import functools
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_BIRDNET_SPECIES
from utils import list2tuple
from utils import sketch

CELL_HEIGHT = 50

@callback(
    Output("species-community-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("species-community-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("species-community-graph", "figure"),
    Input("dataset-select", "value"),
    Input("date-range-current-bounds", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("umap-filter-store", "data"),
    Input("species-community-threshold-slider", "value"),
    Input("species-community-axis-select", "value"),
    Input("species-community-facet-column-select", "value"),
    Input("species-community-facet-row-select", "value"),
    Input("dataset-category-orders", "data"),
    Input("dataset-options", "data"),
    prevent_initial_call=True,
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    file_filter_groups: Dict[str, List],
    threshold: float,
    axis_group: str,
    facet_col: str,
    facet_row: str,
    category_orders: Dict[str, List[str]],
    options: Dict[str, List[str]],
) -> go.Figure:
    data = dispatch(
        FETCH_BIRDNET_SPECIES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )
    data = data[data["confidence"] >= threshold]
    order = (
        data.groupby("species")["confidence"]
        .count()
        .sort_values(ascending=True)
        .index.tolist()
    )
    fig = px.density_heatmap(
        data_frame=data,
        x=axis_group,
        y="species",
        z="confidence",
        histfunc="count",
        histnorm=None,
        text_auto=True,
        facet_col=facet_col,
        facet_row=facet_row,
        color_continuous_scale="Greys",
        category_orders=category_orders,
        labels={
            "species": "Species",
            "confidence": "Occurrence",
            axis_group: options.get(axis_group, {}).get("label", axis_group),
            facet_col: options.get(facet_col, {}).get("label", facet_col),
            facet_row: options.get(facet_row, {}).get("label", facet_row),
        }
    )
    # remove prefix in the facet-wise annotations
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_yaxes(categoryorder="array", categoryarray=order)
    fig.update_layout(
        barmode='stack',
        margin=dict(l=20, r=20, t=80, b=40),
        height=data["species"].nunique() * CELL_HEIGHT,
        title=dict(
            text=f"Species by Site",
            x=0.5,
            y=0.97,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        ),
    )
    return fig
