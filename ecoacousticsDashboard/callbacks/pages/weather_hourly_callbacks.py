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

from api import dispatch, FETCH_WEATHER
from utils import list2tuple

PLOT_HEIGHT = 800

@callback(
    Output("weather-hourly-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("weather-hourly-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("weather-hourly-graph-data", "data"),
    Input("dataset-select", "value"),
    Input("date-range-current-bounds", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def load_data(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
) -> str:
    return dispatch(
        FETCH_WEATHER,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
    ).to_json(
        date_format="iso",
        orient="table",
    )

@callback(
    Output("weather-hourly-graph", "figure"),
    Input("weather-hourly-graph-data", "data"),
    Input("weather-hourly-variable-select", "value"),
    Input("weather-hourly-time-aggregation", "value"),
    Input("weather-hourly-facet-row-select", "value"),
    Input("dataset-category-orders", "data"),
    prevent_initial_call=True,
)
def draw_figure(
    json_data: str,
    weather_variable: str,
    time_agg: str,
    facet_row: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    data = pd.read_json(StringIO(json_data), orient="table")
    data = (
        data[data["variable"] == weather_variable]
        .sort_values("timestamp")
        .groupby(by=["site_name", "location", "recorder", pd.Grouper(key="timestamp", freq=time_agg)])
        .agg({"value": ["mean", "std"]})
        .reset_index()
    )
    data.columns = [
        "_".join(filter(None, col_levels))
        for col_levels in data.columns.to_flat_index()
    ]
    # FIXME: hack due to data discontinuity, can fix once proper data structures on back-end
    facet_row = "site_name" if facet_row == "site" else facet_row

    fig = px.line(
        data_frame=data,
        x="timestamp",
        y="value_mean",
        error_y="value_std",
        color="location",
        facet_row=facet_row,
        markers=True,
        labels=dict(
            timestamp="Time",
            value_mean="value",
        ),
        category_orders=category_orders,
    )

    fig.update_traces(marker=dict(size=4))

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=weather_variable,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    return fig

