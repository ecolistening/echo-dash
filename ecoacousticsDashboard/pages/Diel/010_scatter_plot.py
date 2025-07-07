import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
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
from utils import sketch

PAGE_NAME = 'index-scatter'
PAGE_TITLE = 'Acoustic Descriptor by Time of Day'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Scatter Plot'
)

PLOT_HEIGHT = 800

layout = html.Div([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="index-scatter-colour-select",
                    label="Colour by",
                ),
                DatasetOptionsSelect(
                    id="index-scatter-symbol-select",
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="index-scatter-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="index-scatter-facet-column-select",
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
                            plot_name="index-scatter-graph",
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            grow=True,
            children=dmc.Stack([
                dmc.Text(
                    "Dot Size",
                    size="sm",
                    ta="left",
                ),
                dmc.Slider(
                    id="index-scatter-size-slider",
                    min=1,
                    max=20,
                    step=1,
                    value=6,
                    marks=[
                        {"value": i, "label": f"{i}"}
                        for i in (1, 10, 20)
                    ],
                    persistence=True
                )
            ]),
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id=f"index-scatter-graph"),
    ),
    dbc.Offcanvas(
        id="index-scatter-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-scatter"),
    ),
])

@callback(
    Output("index-scatter-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("index-scatter-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("index-scatter-graph", "figure"),
    State("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("feature-dropdown", "value"),
    Input("index-scatter-size-slider", "value"),
    Input("index-scatter-colour-select", "value"),
    Input("index-scatter-symbol-select", "value"),
    Input("index-scatter-facet-row-select", "value"),
    Input("index-scatter-facet-column-select", "value"),
)
def draw_figure(
    dataset_name: str,
    dates: List,
    locations: List[str],
    feature: str,
    dot_size: int,
    color: str,
    symbol: str,
    facet_row: str,
    facet_col: str,
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

    fig = px.scatter(
        data,
        x='hour',
        y='value',
        hover_name="file",
        hover_data=["timestamp", "path"], # Path last for sound sample modal
        opacity=0.5,
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        category_orders=category_orders,
    )

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(
        height=PLOT_HEIGHT,
        title={
            'text':f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    # Adjust size of index-scatter dots
    fig.update_traces(marker=dict(size=dot_size))

    return fig
