import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import itertools
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES, FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.figure_download_widget import FigureDownloadWidget
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

layout = dmc.Box([
    dcc.Store(id="times-graph-data"),
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
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="times-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="times-symbol-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="times-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="times-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet columns by"
                ),
                dmc.Flex(
                    p="1rem",
                    align="center",
                    justify="right",
                    direction="row",
                    children=[
                        dmc.Group(
                            grow=True,
                            children=[
                                DataDownloadWidget(
                                    graph_data="times-graph-data",
                                ),
                                FigureDownloadWidget(
                                    plot_name="times-graph",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            grow=True,
            children=[
                dmc.Stack([
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
                ]),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
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
    State("dataset-select", "value"),
    State("filter-store", "data"),
    # Input("umap-filter-store", "data"),
    Input("times-size-slider", "value"),
    Input("times-colour-select", "value"),
    Input("times-symbol-select", "value"),
    Input("times-facet-row-select", "value"),
    Input("times-facet-column-select", "value"),
    Input("dataset-category-orders", "data"),
)
def draw_figure(
    dataset_name: str,
    filters: Dict[str, Any],
    # file_filter_groups: Dict[str, List],
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
    category_orders: Dict[str, List[str]],
) -> go.Figure:
    data = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        **{variable: list2tuple(params["variable_range"]) for variable, params in filters["weather_variables"].items()},
        # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )
    fig = px.scatter(
        data_frame=data,
        x="date",
        y="time",
        opacity=0.25,
        hover_name="file_name",
        hover_data=["file_id", "timestamp"],
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        labels=dict(
            date="Date",
            time="Hour",
        ),
        category_orders=category_orders,
    )
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            automargin=True,
            x=0.5,
            y=1.00,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        ),
        scattermode="group",
        scattergap=0.75,
    )
    fig.update_traces(marker=dict(size=dot_size))
    return fig
