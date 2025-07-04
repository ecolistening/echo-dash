import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

import components
from api import dispatch, FETCH_LOCATIONS
from utils.content import get_tabs
from utils.save_plot_fig import get_save_plot

PAGE_NAME = 'map'
PAGE_TITLE = 'Location Map'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Map')

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
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
    dmc.Divider(variant='dotted'),
    dcc.Loading(
        dcc.Graph(id=graph_id),
    ),
    components.Footer(PAGE_NAME),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
)
def update_graph(dataset_name):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=}")

    data = dispatch(
        FETCH_LOCATIONS,
        dataset_name=dataset_name,
    )
    '''
        Calculate Zoom Level for World Map

        https://docs.mapbox.com/help/glossary/zoom-level/#zoom-levels-and-geographical-distance
    '''
    extents = data.describe()
    longitude_range = extents.loc['max', 'longitude'] - extents.loc['min', 'longitude']
    latitude_range = extents.loc['max', 'latitude'] - extents.loc['min', 'latitude']

    # The 111 is a constant to convert decimal degrees to kilometers
    max_bound = max(longitude_range, latitude_range) * 111

    # Formula established by trial-and-error
    zoom = 12 - np.log(max_bound)*1.1

    logger.debug(f"{dataset_name=} {latitude_range=:.4f} {longitude_range=:.4f} {max_bound=:.4f} {np.log(max_bound)=:.4f} {zoom=:.4f}")

    fig = px.scatter_mapbox(
        data,
        lat="latitude",
        lon="longitude",
        hover_name="site",
        hover_data=['timezone'],
        color_discrete_sequence=["red"],
        zoom=zoom,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style="open-street-map",
    )

    return fig
