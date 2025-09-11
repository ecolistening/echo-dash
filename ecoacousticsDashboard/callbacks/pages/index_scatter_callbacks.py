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
from utils import list2tuple, capitalise_each

PLOT_HEIGHT = 800

def register_callbacks():
    @callback(
        Output("index-scatter-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("index-scatter-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("index-scatter-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        # Input("umap-filter-store", "data"),
        Input("index-scatter-size-slider", "value"),
        Input("index-scatter-colour-select", "value"),
        Input("index-scatter-symbol-select", "value"),
        Input("index-scatter-facet-row-select", "value"),
        Input("index-scatter-facet-column-select", "value"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        # file_filter_groups: Dict[str, List],
        dot_size: int,
        color: str,
        symbol: str,
        facet_row: str,
        facet_col: str,
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = dispatch(
            FETCH_ACOUSTIC_FEATURES,
            dataset_name=dataset_name,
            dates=list2tuple(filters["date_range"]),
            feature=filters["current_feature"],
            feature_range=list2tuple(filters["current_feature_range"]),
            **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
            locations=list2tuple(filters["current_sites"]),
            # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
        )
        fig = px.scatter(
            data_frame=data,
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
                value=capitalise_each(filters["current_feature"]),
            ),
            category_orders=category_orders,
        )
        fig.update_traces(marker=dict(size=dot_size))
        fig.update_layout(
            height=PLOT_HEIGHT,
            title=dict(
                text=f"Acoustic Descriptor by Time of Day",
                x=0.5,
                y=0.97,
                font=dict(size=24),
            )
        )
        return fig
