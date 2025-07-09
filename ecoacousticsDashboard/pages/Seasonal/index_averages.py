import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import List, Tuple

from api import (
    dispatch,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_DATASET_CATEGORIES,
)
from components.dataset_options_select import DatasetOptionsSelect
from components.controls_panel import ControlsPanel
from components.figure_download_widget import FigureDownloadWidget
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.acoustic_feature_filter import AcousticFeatureFilter
from components.footer import Footer
from utils import list2tuple

PAGE_NAME = "idx-averages"
PAGE_TITLE = "Seasonal Descriptor Averages"
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Averages"
)

windows_options = [
    { "description": "1 day", "frequency": "1D" },
    { "description": "1 week", "frequency": "1W" },
    { "description": "2 weeks", "frequency": "2W" },
    { "description": "1 month", "frequency": "1ME" },
    { "description": "3 months", "frequency": "3ME" },
    { "description": "6 months", "frequency": "6ME" },
]

layout = html.Div([
    FilterPanel([
        dmc.Group(
            align="start",
            grow=True,
            children=[
                SiteLevelFilter(),
                DateRangeFilter(),
                EnvironmentalFilter(),
            ]
        ),
        dmc.Space(h=10),
        dmc.Group(
            align="start",
            grow=True,
            children=[
                AcousticFeatureFilter(),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                time_aggregation := dmc.SegmentedControl(
                    id="index-averages-time-aggregation",
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
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="index-averages-graph",
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id="index-averages-graph"),
    ),
    dbc.Offcanvas(
        id="index-averages-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-averages"),
    ),
])

@callback(
    Output("index-averages-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("index-averages-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("index-averages-graph", "figure"),
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("feature-dropdown", "value"),
    Input("acoustic-feature-range-slider", "value"),
    Input("index-averages-time-aggregation", "value"),
    # Input(outliers_tickbox, "checked"),
    # Input(colours_tickbox, "checked"),
    # Input(separate_plots_tickbox, "checked"),
)
def update_graph(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    feature: str,
    feature_range: List[float],
    time_agg: str,
    # outliers,
    # colour_locations,
    # separate_plots,
) -> go.Figure:
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        feature=feature,
        # FIXME: hashing floating points will break the LRU cache
        # (1) set a fixed step-size and
        # (2) scale values and pass as integers along with scaling factor
        feature_range=list2tuple(feature_range),
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )
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
            'text': f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    return fig
