import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import List

from api import (
    dispatch,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_DATASET_CATEGORIES,
)
from components.dataset_options_select import DatasetOptionsSelect
from components.controls_panel import ControlsPanel
from components.figure_download_widget import FigureDownloadWidget
from components.footer import Footer
from utils import list2tuple
import components

PAGE_NAME = "index-box-plot"
PAGE_TITLE = "Box Plot of Acoustic Descriptor by Time of Day"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Box Plot"
)

PLOT_HEIGHT = 800

layout = html.Div([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="index-box-colour-select",
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="index-box-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="index-box-facet-column-select",
                    label="Facet columns by"
                ),
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="index-box-graph",
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            children=[
                dmc.Stack([
                    dmc.Text(
                        "Group by Time",
                        size="sm",
                        ta="left",
                    ),
                    dmc.SegmentedControl(
                        id="index-box-time-aggregation",
                        data=[
                            {"value": "time", "label": "15 minutes"},
                            {"value": "hour", "label": "1 hour"},
                            {"value": "dddn", "label": "Dawn-Day-Dusk-Night"}
                        ],
                        value="dddn",
                        persistence=True
                    ),
                ]),
                dmc.Stack([
                    dmc.Chip(
                        "Outliers",
                        id="index-box-outliers-tickbox",
                        value="outlier",
                        checked=True,
                        persistence=True,
                    ),
                ]),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id="index-box-graph"),
    ),
    dbc.Offcanvas(
        id="index-box-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-box"),
    ),
    # FIXME
    # components.SoundSampleModal(
    #     PAGE_NAME,
    # ),
])

@callback(
    Output("index-box-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("index-box-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open


@callback(
    Output("index-box-graph", "figure"),
    State("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("feature-dropdown", "value"),
    Input("index-box-time-aggregation", "value"),
    Input("index-box-outliers-tickbox", "checked"),
    Input("index-box-colour-select", "value"),
    Input("index-box-facet-row-select", "value"),
    Input("index-box-facet-column-select", "value"),
)
def update_graph(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    feature: str,
    time_agg: str,
    outliers: bool,
    color: str,
    facet_row: str,
    facet_col: str,
) -> go.Figure:
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        feature=feature,
    ).sort_values(by='recorder')

    data = data.assign(
        time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0,
        hour=data.timestamp.dt.hour,
        minute=data.timestamp.dt.minute
    )

    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )

    fig = px.box(
        data,
        x=time_agg,
        y='value',
        hover_name='file',
        hover_data=['file', 'timestamp', 'path'], # Path last for sound sample modal
        height=PLOT_HEIGHT,
        color=color,
        facet_row=facet_row,
        facet_col=facet_col,
        # facet_col_wrap=4,
        points='outliers' if outliers else False,
        category_orders=category_orders,
    )

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(
        title={
            'text':f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    return fig
