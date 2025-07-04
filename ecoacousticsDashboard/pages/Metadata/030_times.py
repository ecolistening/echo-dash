import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

import components
from api import (
    dispatch,
    FETCH_FILES,
    FETCH_DATASET_CATEGORIES,
)
from utils import list2tuple
from utils.content import get_tabs

PAGE_NAME = 'times'
PAGE_TITLE = 'Recording Times'
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Times'
)

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
locations_hierarchy_id = "checklist-locations-hierarchy"

graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-select"
symbol_select_id = f"{PAGE_NAME}-symbol-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
size_slider_id = f"{PAGE_NAME}-size-slider"

layout = html.Div([
    dmc.Group(
        grow=True,
        style={"margin-bottom": "0.5em"},
        children=[
            components.ColourSelect(
                id=colour_select_id,
                default="location",
            ),
            components.SymbolSelect(
                id=symbol_select_id,
            ),
            components.RowFacetSelect(
                id=row_facet_select_id,
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
            ),
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
    dmc.Grid([
        dmc.Col(
            span=4,
            children=[
                dmc.Text(
                    "Dot Size",
                    size="sm",
                    align="left",
                ),
                dmc.Slider(
                    id=size_slider_id,
                    min=1,
                    max=20,
                    step=1,
                    value=4,
                    marks=[
                        {"value": i, "label": f"{i}"}
                        for i in (1, 10, 20)
                    ],
                    persistence=True
                )
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id=graph_id),
    ),
    components.Footer(PAGE_NAME),
    # TODO: fixme
    # get_modal_sound_sample(PAGE_NAME),
])

@callback(
    Output(graph_id, "figure"),
    State(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input({"type": locations_hierarchy_id, "index": ALL}, "value"),
    Input(colour_select_id, "value"),
    Input(symbol_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(size_slider_id, "value"),
    prevent_initial_call=True,
)
def update_graph(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    colour_by: str,
    symbol_by: str,
    row_facet: str,
    col_facet: str,
    dot_size: int
):
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"{dataset_name=} dates:{len(dates)} locations:{len(locations)} "
        f"{colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=}"
    )

    data = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )

    fig = px.scatter(
        data,
        x='date',
        y='hour_float',
        opacity=0.25,
        hover_name="file_name",
        hover_data=["file_path"],
        color=colour_by,
        symbol=symbol_by,
        facet_row=row_facet,
        facet_col=col_facet,
        labels=dict(
            date="Date",
            hour_float="Hour"
        ),
        category_orders=category_orders,
    )

    fig.update_layout()

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        ),
        scattermode="group",
        scattergap=0.75,
    )

    fig.update_traces(marker=dict(size=dot_size))

    return fig
