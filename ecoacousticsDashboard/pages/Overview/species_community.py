import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from utils.data import dataset_loader, filter_data
from utils.plot_filter_menu import get_filter_drop_down

PAGE_NAME = 'species-community'
PAGE_TITLE = 'Species Community'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Species Community')

colour_select, row_facet_select, col_facet_select = get_filter_drop_down(
    PAGE_NAME,
    colour_by_cat=True,
    include_symbol=False,
    colour_default='site_name',
    row_facet_default='site_name',
    col_facet_default=None
)

filter_group = dmc.Group(children=[colour_select, row_facet_select, col_facet_select])

graph = dcc.Graph(id=f'{PAGE_NAME}-graph')

layout = html.Div([
    html.Div([html.H1(PAGE_TITLE)]),
    html.Hr(),
    dmc.Divider(variant='dotted'),
    filter_group,
    graph,
])

@callback(
    Output(f'{PAGE_NAME}-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input(colour_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
)
def update_figure(dataset_name, locations, colour_by, row_facet, col_facet):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    import code; code.interact(local=locals())
    data = filter_data(dataset.birdnet_species_probs, locations=locations)

    fig = px.violin(
        data,
        x="common_name",
        y="confidence",
        color=colour_by,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=dataset.category_orders(),
        box=True,
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
