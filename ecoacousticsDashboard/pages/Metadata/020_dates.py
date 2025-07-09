import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import pandas as pd
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from plotly_calplot import calplot
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_FILES,
)
from components.figure_download_widget import FigureDownloadWidget
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.footer import Footer
from utils import list2tuple

PAGE_NAME = 'dates'
PAGE_TITLE = 'Recording Dates'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Dates')

layout = html.Div([
    FilterPanel([
        dmc.Group(
            align="start",
            grow=True,
            children=[
                dmc.Accordion(
                    chevronPosition="right",
                    variant="separated",
                    radius="sm",
                    children=[
                        dmc.AccordionItem(
                            value="acoustic-features",
                            children=[
                                dmc.AccordionControl("Acoustic Feature"),
                                dmc.AccordionPanel(
                                    children=[
                                        dmc.Stack(
                                            justify="flex-start",
                                            children=[
                                                dmc.Box([
                                                    dmc.Text("Select an acoustic feature", size="sm"),
                                                    dmc.Select(
                                                        id="feature-dropdown",
                                                        searchable=True,
                                                        clearable=False,
                                                        allowDeselect=False,
                                                        nothingFoundMessage="No options found...",
                                                    ),
                                                ]),
                                                dmc.Divider(
                                                    variant="solid",
                                                    orientation="vertical",
                                                ),
                                                dmc.Box(
                                                    # m=10,
                                                    children=[
                                                        dmc.Text("Select a value range", size="sm"),
                                                        dcc.RangeSlider(
                                                            id="acoustic-feature-range-slider",
                                                            min=0,
                                                            max=100,
                                                            value=[0, 100],
                                                            allowCross=False,
                                                        ),
                                                        dmc.Box(
                                                            children=[
                                                                dmc.Text(
                                                                    "Current Range: ",
                                                                    size="sm",
                                                                    span=True
                                                                ),
                                                                dmc.Text(
                                                                    id="acoustic-feature-range-bounds",
                                                                    size="sm",
                                                                    span=True
                                                                ),
                                                            ]
                                                        )
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                ),
                dmc.Accordion(
                    chevronPosition="right",
                    variant="separated",
                    radius="sm",
                    children=[
                        dmc.AccordionItem(
                            value="date-range",
                            children=[
                                dmc.AccordionControl("Date Range"),
                                dmc.AccordionPanel(
                                    children=[
                                        dmc.Stack(
                                            justify="flex-start",
                                            children=[
                                                dmc.Text("Filter by Date"),
                                                dmc.DatePicker(
                                                    id="date-picker",
                                                    type="range",
                                                    minDate=dt.date(1970, 1, 1),
                                                    maxDate=dt.date.today(),
                                                    value=[dt.date(1970, 1, 1), dt.date.today()],
                                                    persistence=True,
                                                    allowDeselect=False,
                                                    numberOfColumns=2,
                                                    columnsToScroll=1,
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                ),
            ]
        ),
        dmc.Space(h=10),
        dmc.Group(
            align="start",
            grow=True,
            children=[
                dmc.Accordion(
                    chevronPosition="right",
                    variant="separated",
                    radius="sm",
                    children=[
                        dmc.AccordionItem(
                            value="site-level",
                            children=[
                                dmc.AccordionControl("Site Level"),
                                dmc.AccordionPanel(
                                    id="site-level-filter-group",
                                    children=[]
                                )
                            ]
                        )
                    ],
                ),
                dmc.Accordion(
                    chevronPosition="right",
                    variant="separated",
                    radius="sm",
                    children=[
                        dmc.AccordionItem(
                            value="environmental",
                            children=[
                                dmc.AccordionControl("Environmental"),
                                dmc.AccordionPanel(
                                    children=[
                                        dmc.Stack(
                                            justify="flex-start",
                                            children=[
                                                dmc.Box(
                                                    children=[
                                                        dmc.Text("Select a temperature range", size="sm"),
                                                        dcc.RangeSlider(
                                                            id="temperature-range-slider",
                                                            min=0,
                                                            max=100,
                                                            value=[0, 100],
                                                            allowCross=False,
                                                        ),
                                                    ]
                                                ),
                                                dmc.Box(
                                                    children=[
                                                        dmc.Text("Select a precipitation range", size="sm"),
                                                        dcc.RangeSlider(
                                                            id="precipitation-range-slider",
                                                            min=0,
                                                            max=100,
                                                            value=[0, 100],
                                                            allowCross=False,
                                                        ),
                                                    ]
                                                ),
                                                dmc.Box(
                                                    children=[
                                                        dmc.Text("Select a wind speed range", size="sm"),
                                                        dcc.RangeSlider(
                                                            id="wind-speed-range-slider",
                                                            min=0,
                                                            max=100,
                                                            value=[0, 100],
                                                            allowCross=False,
                                                        ),
                                                    ]
                                                ),
                                                dmc.Box(
                                                    children=[
                                                        dmc.Text("Select a snowfall range", size="sm"),
                                                        dcc.RangeSlider(
                                                            id="snowfall-range-slider",
                                                            min=0,
                                                            max=100,
                                                            value=[0, 100],
                                                            allowCross=False,
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                ),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="dates-graph",
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id="dates-graph"),
    ),
    dbc.Offcanvas(
        id="dates-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("dates"),
    ),
])

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
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({'type': "checklist-locations-hierarchy", 'index': ALL}, 'value'),
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
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
