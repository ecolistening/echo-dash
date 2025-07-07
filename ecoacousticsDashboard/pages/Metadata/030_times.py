import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_FILES,
    FETCH_DATASET_CATEGORIES,
)
from components.dataset_options_select import DatasetOptionsSelect
from components.footer import Footer
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

layout = html.Div([
    dmc.Group(
        grow=True,
        children=[
            DatasetOptionsSelect(
                id="times-colour-select",
                label="Colour by"
            ),
            DatasetOptionsSelect(
                id="times-symbol-select",
                label="Symbol by"
            ),
            DatasetOptionsSelect(
                id="times-facet-row-select",
                label="Facet rows by"
            ),
            DatasetOptionsSelect(
                id="times-facet-column-select",
                label="Facet columns by"
            ),
        ],
    ),
    dmc.Grid([
        dmc.GridCol(
            span=4,
            children=[
                dmc.Text(
                    "Dot Size",
                    size="sm",
                    ta="left",
                ),
                dmc.Slider(
                    id="times-size-slider",
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
        dcc.Graph(id="times-graph"),
    ),
    dbc.Offcanvas(
        id="times-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("times"),
    ),
    # TODO: fixme
    # get_modal_sound_sample(PAGE_NAME),
])

@callback(
    Output("times-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("times-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("times-graph", "figure"),
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({'type': "checklist-locations-hierarchy", 'index': ALL}, 'value'),
    Input("times-size-slider", "value"),
    Input("times-colour-select", "value"),
    Input("times-symbol-select", "value"),
    Input("times-facet-row-select", "value"),
    Input("times-facet-column-select", "value"),
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
) -> go.Figure:
    triggered_id = ctx.triggered_id
    action = FETCH_FILES
    params = dict(
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations)
    )
    logger.debug(f"{triggered_id=} {action=} {params=}")
    data = dispatch(action, **params)

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
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        labels=dict(
            date="Date",
            hour_float="Hour"
        ),
        category_orders=category_orders,
    )

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
