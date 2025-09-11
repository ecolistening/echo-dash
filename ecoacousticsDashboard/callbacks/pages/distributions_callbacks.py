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
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES
from utils import list2tuple, capitalise_each

PLOT_HEIGHT = 800

def register_callbacks():
    @callback(
        Output("distributions-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("distributions-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("distributions-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        # Input("umap-filter-store", "data"),
        Input("distributions-colour-select", "value"),
        Input("distributions-facet-row-select", "value"),
        Input("distributions-facet-column-select", "value"),
        Input("distributions-normalised-tickbox", "checked"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        # file_filter_groups: Dict[str, List],
        color: str,
        facet_row: str,
        facet_col: str,
        normalised: bool,
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        if not len(filters):
            return no_update
        logger.debug(filters)
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
        fig = px.histogram(
            data_frame=data,
            x="value",
            marginal="rug",
            opacity=0.75,
            color=color,
            facet_row=facet_row,
            facet_col=facet_col,
            histnorm="percent" if normalised else None,
            labels=dict(
                value=capitalise_each(filters["current_feature"]),
            ),
            category_orders=category_orders,
        )
        title_text = (
            f"{capitalise_each(filters['current_feature'])} | "
            f"{filters['date_range'][0]} - {filters['date_range'][1]}"
        )
        fig.update_layout(
            height=PLOT_HEIGHT,
            title=dict(
                text=title_text,
                x=0.5,
                y=0.97,
                font=dict(size=24),
            )
        )
        return fig
