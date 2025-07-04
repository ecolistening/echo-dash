import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from dash_iconify import DashIconify
from loguru import logger

import components
from api import (
    dispatch,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_DATASET_CATEGORIES,
)
from utils import list2tuple
from utils.content import get_tabs

PAGE_NAME = 'distributions'
PAGE_TITLE = 'Soundscape Descriptor Distributions'
PLOTHEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Distributions'
)

graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-facet-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
norm_tickbox_id = f"{PAGE_NAME}-normalised-tickbox"

layout = html.Div([
    dmc.Group(
        grow=True,
        style={"margin-bottom": "0.5em"},
        children=[
            components.ColourSelect(
                id=colour_select_id,
                categorical=True,
                default="location",
            ),
            components.RowFacetSelect(
                id=row_facet_select_id,
                default="location",
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
                default="dddn",
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
        ]
    ),
    dmc.Group([
        html.Div([
            dmc.Chip(
                'Normalised',
                id=norm_tickbox_id,
                value='normalised',
                checked=False,
                persistence=True,
            )
        ]),
    ], grow=True),
    dcc.Loading(
        dcc.Graph(id=f'{PAGE_NAME}-graph'),
    ),
    dmc.Grid(
        children=[
            dmc.Col(get_tabs(PAGE_NAME), span=8),
        ],
        gutter="xl",
    ),
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGE_NAME}-graph', 'figure'),
    State('dataset-select', 'value'),
    Input('date-picker', 'value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input('feature-dropdown', 'value'),
    Input(colour_select_id, 'value'),
    Input(row_facet_select_id, 'value'),
    Input(col_facet_select_id, 'value'),
    Input(norm_tickbox_id, 'checked'),

    prevent_initial_call=True,
)
def update_graph(
    dataset_name,
    dates,
    locations,
    feature,
    colour_by,
    row_facet,
    col_facet,
    normalised
) -> go.Figure:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"{dataset_name=} dates:{len(dates)} locations:{len(locations)} "
        f"{feature=} {colour_by=} {row_facet=} {col_facet=} {normalised=}"
    )

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
        data, x='value', marginal='rug', opacity=0.75, height=PLOTHEIGHT,
        color=colour_by,
        facet_row=row_facet,
        facet_col=col_facet,
        histnorm='percent' if normalised else None,
        category_orders=category_orders,
    )

    # Add centered title
    fig.update_layout(title={'text':f"{PAGE_TITLE} ({feature})",
                             'x':0.5,
                             'y':0.97,
                             'font':{'size':24}
                             })

    return fig
