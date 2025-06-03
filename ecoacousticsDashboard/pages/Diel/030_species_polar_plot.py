import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.plot_filter_menu import get_filter_drop_down

PAGE_NAME = 'species-polar-plot'
PAGE_TITLE = 'Polar Plot of Species Occurrence by Time of Day'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Species Occurrence Polar Plot')

dataset = dataset_loader.get_dataset(ds)
# TODO: use species_id
species_list = dataset.species_predictions.common_name.unique()
species_default = species_list[0]

colour_select, row_facet_select, col_facet_select = get_filter_drop_down(
    PAGE_NAME,
    colour_by_cat=True,
    include_symbol=False,
    colour_default='hour',
    row_facet_default='month',
    col_facet_default='weekday',
)

species_select = dmc.Select(
    id=f'{PAGE_NAME}-species-select',
    label="Select species",
    value=species_default,
    searchable=True,
    clearable=False,
    style={"width": 200},
    persistence=True,
    data=[
        {"value": common_name, "label": common_name }
        for common_name in species_list
    ],
)

filter_group = dmc.Group(children=[colour_select, row_facet_select, col_facet_select, species_select])

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
    Input(species_select, component_property='value'),
)
def update_figure(dataset_name, locations, colour_by, row_facet, col_facet, species_name):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.species_predictions[dataset.species_predictions.common_name == species_name], locations=locations)

    fig = px.bar_polar(
        data,
        r="confidence",
        theta="hour",
        width="confidence",
        color=colour_by,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=DatasetDecorator(dataset).category_orders(),
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

