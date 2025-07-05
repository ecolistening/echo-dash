import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objs as go

from dash import html, ctx, dcc, callback
from dash import Output, State, Input, ALL
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
    name='Distributions',
)

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
feature_select_id = "feature-dropdown"
locations_hierarchy_id = "checklist-locations-hierarchy"

graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-facet-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
norm_tickbox_id = f"{PAGE_NAME}-normalised-tickbox"

layout = html.Div([
    components.TopBar(
        dataset_id=dataset_select_id,
        graph_id=graph_id,
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
        dcc.Graph(
            id=graph_id
        ),
    ),
    dbc.Offcanvas(
        id="page-info",
        is_open=False,
        placement="bottom",
        children=components.Footer(PAGE_NAME),
    ),
])


# Add controls to build the interaction
@callback(
    Output(graph_id, 'figure'),
    State(dataset_select_id, 'value'),
    Input(date_picker_id, 'value'),
    Input({'type': locations_hierarchy_id, 'index': ALL}, 'value'),
    Input(feature_select_id, 'value'),
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

    fig.update_layout(
        title={
            'text':f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    return fig
