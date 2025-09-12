import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import functools
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc
from dash import Output, Input, State, ALL, MATCH
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_BIRDNET_SPECIES
from utils import list2tuple, send_download
from utils import sketch

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_BIRDNET_SPECIES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )

plot_types = {
    "Scatter": functools.partial(
        sketch.scatter,
        x='hour',
        y='richness',
        marker=dict(
            size=10,
            opacity=1.0,
            color="rgba(133, 143, 249, 1.0)",
        ),
        trace_height=400,
    ),
    "Scatter Polar": functools.partial(
        sketch.scatter_polar,
        r="richness",
        theta="hour",
        mode="markers",
        marker=dict(
            size=10,
            opacity=1.0,
            color="rgba(133, 143, 249, 1.0)",
        ),
        fill="toself",
        showlegend=False,
        radialaxis=dict(
            showticklabels=True,
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=(angles := list(range(0, 360, 45))),
            ticktext=[f"{int(angle / 360 * 24):02d}:00" for angle in angles],
            direction="clockwise",
            rotation=90,
            ticks=""
        ),
        trace_height=400,
    ),
    "Bar Polar": functools.partial(
        sketch.bar_polar,
        r="richness",
        theta="hour",
        marker_line_width=2,
        opacity=0.8,
        showlegend=False,
        marker=dict(
            color="rgba(133, 143, 249, 0.6)",
            line=dict(color="rgba(133, 143, 249, 1.0)", width=2)
        ),
        radialaxis=dict(
            showticklabels=True,
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=(angles := list(range(0, 360, 45))),
            ticktext=[f"{int(angle / 360 * 24):02d}:00" for angle in angles],
            direction="clockwise",
            rotation=90,
            ticks=""
        ),
        trace_height=400,
    ),
}

def register_callbacks():
    from dash import callback, ctx, no_update

    @callback(
        Output("species-richness-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("species-richness-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("species-richness-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("species-richness-plot-type-select", "value"),
        Input("species-richness-threshold-slider", "value"),
        Input("species-richness-facet-row-select", "value"),
        Input("species-richness-facet-column-select", "value"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        plot_type: str,
        threshold: str,
        facet_row: str,
        facet_col: str,
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = fetch_data(dataset_name, filters)
        data = (
            data[data["confidence"] >= threshold]
            .groupby(list(filter(None, set(["hour", facet_row, facet_col]))))["species"]
            .nunique()
            .reset_index(name="richness")
        )
        # TODO: refactor
        plot = plot_types[plot_type]
        fig = plot(
            data_frame=data,
            facet_row=facet_row,
            facet_col=facet_col,
            category_orders=category_orders,
        )
        fig.update_layout(
            barmode='stack',
            height=PLOT_HEIGHT,
            title=dict(
                text=f"Polar Plot of Species Richness by Time of Day",
                x=0.5,
                y=0.97,
                font=dict(size=24),
            )
        )
        return fig

    @callback(
        Output("species-richness-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "species-richness-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        )
