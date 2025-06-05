import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from utils.data import dataset_loader, filter_data, DatasetDecorator
import components

PAGE_NAME = 'species-community'
PAGE_TITLE = 'Species Community'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Species Community'
)

PLOT_HEIGHT = 800

dataset_select_id = "dataset-select"
graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"

layout = html.Div([
    html.Div([
        html.H1(PAGE_TITLE)
    ]),
    html.Hr(),
    dmc.Divider(variant="dotted"),
    dmc.Group(
        children=[
            components.ColourSelect(
                id=colour_select_id,
                default="location",
            ),
            components.RowFacetSelect(
                id=row_facet_select_id,
                default=None,
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
                default=None,
            ),
        ]
    ),
    dcc.Graph(id=graph_id),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(colour_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
)
def update_figure(dataset_name, locations, colour_by, row_facet, col_facet):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.species_predictions, locations=locations)
    decorator = DatasetDecorator(dataset)

    fig = px.box(
        data,
        x="common_name",
        y="confidence",
        color=colour_by,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=decorator.category_orders(),
        points=False,
    )
    layout_params = dict(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24)
        )
    )
    fig.update_layout(layout_params)
    return fig
