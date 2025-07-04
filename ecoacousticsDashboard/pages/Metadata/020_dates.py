import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from plotly_calplot import calplot
from typing import Any, Dict, List, Tuple

import components
from api import (
    dispatch,
    FETCH_FILES,
)
from utils import list2tuple

PAGE_NAME = 'dates'
PAGE_TITLE = 'Recording Dates'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Dates')

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
locations_hierarchy_id = "checklist-locations-hierarchy"
graph_id = f"{PAGE_NAME}-graph"

layout = html.Div([
    dmc.Group(
        grow=True,
        style={"margin-bottom": "0.5em"},
        children=[
            html.Div(
                style={
                    "padding": "1rem",
                    "display": "flex",
                    "align-content": "center",
                    "justify-content": "right",
                },
                children=dmc.Group(
                    grow=True,
                    children=[
                        dmc.HoverCard(
                            children=[
                                dmc.HoverCardTarget(
                                    children=dmc.ActionIcon(
                                        DashIconify(
                                            icon="uil:image-download",
                                            width=24,
                                        ),
                                        id="image-download-icon",
                                        variant="light",
                                        color="blue",
                                        size="lg",
                                        n_clicks=0,
                                    ),
                                ),
                                dmc.HoverCardDropdown(
                                    children=[
                                        dmc.Text("Download image as..."),
                                        components.FigureDownloader(graph_id),
                                    ]
                                )
                            ],
                        ),
                        dmc.HoverCard(
                            children=[
                                dmc.HoverCardTarget(
                                    children=dmc.ActionIcon(
                                        DashIconify(
                                            icon="uil:file-download-alt",
                                            width=24,
                                        ),
                                        id="export-data-icon",
                                        variant="light",
                                        color="blue",
                                        size="lg",
                                        n_clicks=0,
                                    ),
                                ),
                                dmc.HoverCardDropdown(
                                    children=[
                                        dmc.Text("Export filtered data as..."),
                                        dmc.Group(
                                            grow=True,
                                            children=[
                                                dmc.Button("csv", variant="filled", id='dl_csv'),
                                                dmc.Button("excel", variant="filled", id='dl_xls'),
                                                dmc.Button("json", variant="filled", id='dl_json'),
                                                dmc.Button("parquet", variant="filled", id='dl_parquet'),
                                            ],
                                        )
                                    ]
                                )
                            ],
                        ),
                        dmc.HoverCard(
                            children=[
                                dmc.HoverCardTarget(
                                    children=dmc.ActionIcon(
                                        DashIconify(
                                            icon="uil:info-circle",
                                            width=24,
                                        ),
                                        id="info-icon",
                                        variant="light",
                                        color="blue",
                                        size="lg",
                                        n_clicks=0,
                                    ),
                                ),
                                dmc.HoverCardDropdown(
                                    dmc.Text("View page information"),
                                )
                            ],
                        ),
                    ],
                ),
            ),
        ],
    ),
    dcc.Loading(
        dcc.Graph(id=graph_id),
    ),
    components.Footer(PAGE_NAME),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input({'type': locations_hierarchy_id, 'index': ALL}, 'value'),
)
def update_graph(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
) -> go.Figure:
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} dates:{len(dates)} locations:{len(locations)}")

    # FIXME: refactor into a unique API call
    data = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
    )
    data = data.groupby('date').agg('count').reset_index()

    fig = calplot(
        data,
        x='date',
        y='file'
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    return fig
