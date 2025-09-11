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
from plotly_calplot import calplot
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES
from utils import list2tuple

PLOT_HEIGHT = 800

def register_callbacks():
    @callback(
        Output("dates-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("dates-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("dates-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        # Input("umap-filter-store", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        # file_filter_groups: Dict[int, List[str]],
    ) -> go.Figure:
        data = dispatch(
            FETCH_FILES,
            dataset_name=dataset_name,
            dates=list2tuple(filters["date_range"]),
            locations=list2tuple(filters["current_sites"]),
            **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
            # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
        )
        data = (
            data
            .groupby("date")
            .agg("count")
            .reset_index()
        )
        fig = calplot(
            data,
            x="date",
            y="file_name"
        )
        fig.update_layout(
            height=PLOT_HEIGHT,
            title=dict(
                text='Recording Dates',
                automargin=True,
                x=0.5,
                y=1.00,
                xanchor="center",
                yanchor="top",
                font=dict(size=24),
            )
        )
        return fig
