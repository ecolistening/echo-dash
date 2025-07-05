import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import List, Tuple

import components
from api import (
    dispatch,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_DATASET_CATEGORIES,
)
from utils import list2tuple

PAGE_NAME = "idx-averages"
PAGE_TITLE = "Seasonal Descriptor Averages"
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Averages"
)

# global selectors
dataset_select_id = "dataset-select"
feature_select_id = "feature-dropdown"
locations_hierarchy_id = "checklist-locations-hierarchy"
date_picker_id = "date-picker"

# page-specific selectors
graph_id = f"{PAGE_NAME}-graph"
time_aggregation_id = f"{PAGE_NAME}-time-aggregation"

windows_options = [
    { "description": "1 day", "frequency": "1D" },
    { "description": "1 week", "frequency": "1W" },
    { "description": "2 weeks", "frequency": "2W" },
    { "description": "1 month", "frequency": "1ME" },
    { "description": "3 months", "frequency": "3ME" },
    { "description": "6 months", "frequency": "6ME" },
]

layout = html.Div([
    components.TopBar(
        dataset_id=dataset_select_id,
        graph_id=graph_id,
        children=[
            time_aggregation := dmc.SegmentedControl(
                id=time_aggregation_id,
                data=[
                    {"value": opt["frequency"], "label": opt["description"]}
                    for opt in windows_options
                ],
                value=windows_options[3]["frequency"],
                persistence=True,
            ),
            # colours_tickbox := dmc.Chip(
            #     'Colour by Recorder',
            #     value='colour',
            #     checked=True,
            #     persistence=True,
            #     id='colour-locations'
            # ),
            # outliers_tickbox := dmc.Chip(
            #     'Outliers',
            #     value='outlier',
            #     checked=True,
            #     persistence=True,
            #     id='outliers-tickbox'
            # )
            # separate_plots_tickbox := dmc.Chip(
            #     'Plot per Recorder',
            #     value='subplots',
            #     checked=False,
            #     persistence=True,
            #     id='separate-plots'
            # )
        ],
    ),
    dcc.Loading(
        dcc.Graph(id=f'{PAGE_NAME}-graph'),
    ),
    dbc.Offcanvas(
        id="page-info",
        is_open=False,
        placement="bottom",
        children=components.Footer(PAGE_NAME),
    ),
])


@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input({"type": locations_hierarchy_id, "index": ALL}, "value"),
    Input(feature_select_id, "value"),
    Input(time_aggregation_id, "value"),
    # Input(outliers_tickbox, "checked"),
    # Input(colours_tickbox, "checked"),
    # Input(separate_plots_tickbox, "checked"),
)
def update_graph(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    feature_name: str,
    time_agg: str,
    # outliers,
    # colour_locations,
    # separate_plots,
) -> go.Figure:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"{dataset_name=} dates:{len(dates)} locations:{len(locations)} "
        f"{feature_name=} {time_agg=}"
    )
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )
    # FIXME: there's something off with this!
    data = (
        data
        .sort_values("timestamp")
        .groupby(by=[
            "location",
            "recorder",
            "feature",
            "dddn",
            pd.Grouper(key="timestamp", freq=time_agg)
        ])
        .agg({"value": ["mean", "std"]})
        .reset_index()
    )
    data.columns = [
        "_".join(filter(None, col_levels))
        for col_levels in data.columns.to_flat_index()
    ]

    fig = px.line(
        data,
        x="timestamp",
        y="value_mean",
        error_y="value_std",
        color="location",
        facet_row="dddn",
        markers=True,
        labels=dict(
            timestamp="Time",
            value_mean="Value",
        ),
        category_orders=category_orders,
    )
    fig.update_traces(marker={'size': 4})

    fig.update_layout(
        height=PLOT_HEIGHT,
        title={
            'text': f"{PAGE_TITLE} ({feature_name})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    return fig
