import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback
from dash import Output, State, Input, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

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
from utils.content import get_tabs

PAGE_NAME = 'distributions'
PAGE_TITLE = 'Soundscape Descriptor Distributions'
PLOTHEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Distributions',
)

layout = html.Div([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="distributions-colour-select",
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="distributions-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="distributions-facet-column-select",
                    label="Facet columns by"
                ),
                html.Div([
                    dmc.Chip(
                        'Normalised',
                        id="distributions-normalised-tickbox",
                        value='normalised',
                        checked=False,
                        persistence=True,
                    )
                ]),
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="distributions-graph",
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(
            id="distributions-graph"
        ),
    ),
    dbc.Offcanvas(
        id="distributions-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("distributions"),
    ),
])

@callback(
    Output("distributions-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("distributions-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open


@callback(
    Output("distributions-graph", 'figure'),
    State("dataset-select", 'value'),
    Input("date-picker", 'value'),
    Input({'type': "checklist-locations-hierarchy", 'index': ALL}, 'value'),
    Input("feature-dropdown", 'value'),
    Input("distributions-colour-select", 'value'),
    Input("distributions-facet-row-select", 'value'),
    Input("distributions-facet-column-select", 'value'),
    Input("distributions-normalised-tickbox", 'checked'),
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    feature: str,
    color: str,
    facet_row: str,
    facet_col: str,
    normalised: bool,
) -> go.Figure:
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        feature=feature,
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )

    fig = px.histogram(
        data,
        x='value',
        marginal='rug',
        opacity=0.75,
        height=PLOTHEIGHT,
        color=color,
        facet_row=facet_row,
        facet_col=facet_col,
        histnorm='percent' if normalised else None,
        category_orders=category_orders,
    )

    fig.update_layout(
        title={
            'text':f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    return fig
