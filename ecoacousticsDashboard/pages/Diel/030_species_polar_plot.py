import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.plot_filter_menu import get_filter_drop_down
from utils import sketch as plt

PAGE_NAME = 'species-polar-plot'
PAGE_TITLE = 'Polar Plot of Species Occurrence Probability by Time of Day'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Species Occurrence Polar Plot')

dataset = dataset_loader.get_dataset(ds)
# TODO: use species_id
species_list = sorted(dataset.species_predictions.common_name.unique())
species_default = species_list[0]

colour_select, row_facet_select, col_facet_select = get_filter_drop_down(
    PAGE_NAME,
    colour_by_cat=True,
    include_symbol=False,
    colour_default='weekday',
    row_facet_default='location',
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
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=} {species_name=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    species_data = dataset.species_predictions[dataset.species_predictions.common_name == species_name]
    data = filter_data(species_data, locations=locations)

    fig = plt.bar_polar(
        data,
        r="confidence",
        theta="hour",
        row_facet=row_facet,
        col_facet=col_facet,
        marker_line_color="black",
        marker_line_width=2,
        opacity=0.8,
        showlegend=False,
        radialaxis=dict(
            range=[0, 1],
            showticklabels=True,
            title="Confidence",
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=[0, 90, 180, 270],
            ticktext=["00:00", "06:00", "12:00", "18:00"],
            direction="clockwise",
            title="Hour of Day",
            rotation=90,
            ticks=""
        )
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin=dict(r=150),
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24)
        ),
    )

    return fig

