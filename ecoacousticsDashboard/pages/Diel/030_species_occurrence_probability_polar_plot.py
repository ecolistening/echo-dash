import dash
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.plot_filter_menu import get_filter_drop_down
from utils import sketch

PAGE_NAME = "species-occurrence-probability-polar-plot"
PAGE_TITLE = "Polar Plot of Species Occurrence Probability by Time of Day"
MENU_NAME = "Polar Species Probability by Time of Day"
PLOT_HEIGHT = 800

dash.register_page(__name__, title=PAGE_TITLE, name=MENU_NAME)

dataset = dataset_loader.get_dataset(ds)
# TODO: use species_id
species_list = sorted(dataset.species_predictions.common_name.unique())
species_default = species_list[0]

colour_select, row_facet_select, col_facet_select = get_filter_drop_down(
    PAGE_NAME,
    colour_by_cat=True,
    include_symbol=False,
    colour_default="weekday",
    row_facet_default="location",
    col_facet_default="weekday",
)

species_select = dmc.Select(
    id=f"{PAGE_NAME}-species-select",
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

plot_types = {
    "Scatter Polar": sketch.scatter_polar,
    "Bar Polar": sketch.bar_polar,
}
plot_type_kwargs = {
    "Scatter Polar": dict(
        mode="markers",
        marker=dict(size=6, opacity=0.5),
    ),
    "Bar Polar": dict(
        marker_line_width=2,
    ),
}
plot_type_select = dmc.Select(
    id=f"{PAGE_NAME}-plot-type-select",
    label="Select polar plot type",
    value="Bar Polar",
    searchable=True,
    clearable=False,
    style={"width": 200},
    persistence=True,
    data=[
        {"value": plot_type, "label": plot_type }
        for plot_type in plot_types.keys()
    ],
)

opacity_slider_text = dmc.Text("Opacity", size="sm", align="right")
opacity_slider = dmc.Slider(
    id=f'{PAGE_NAME}-plot-options-opacity',
    min=0, max=100, step=5, value=50,
    marks=[
        {'value': i, 'label': f'{i}%'} for i in range(0, 101, 20)
    ],
    persistence=True
)

filter_group = dmc.Group(children=[plot_type_select, species_select, colour_select, row_facet_select, col_facet_select, opacity_slider_text, opacity_slider], grow=True)

graph = dcc.Graph(id=f"{PAGE_NAME}-graph")

layout = html.Div([
    html.Div([html.H1(PAGE_TITLE)]),
    html.Hr(),
    dmc.Divider(variant="dotted"),
    filter_group,
    graph,
])

@callback(
    Output(f"{PAGE_NAME}-graph", "figure"),
    Input("dataset-select", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(colour_select, "value"),
    Input(row_facet_select, "value"),
    Input(col_facet_select, "value"),
    Input(species_select, "value"),
    Input(plot_type_select, "value"),
    Input(opacity_slider, "value"),
)
def update_figure(dataset_name, locations, colour_by, row_facet, col_facet, species_name, plot_type, opacity):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=} {species_name=} {plot_type=} {opacity=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = dataset.views.species_probability_by_hour(species_name, row_facet, col_facet)
    data = filter_data(data, locations=locations)
    category_orders = DatasetDecorator(dataset).category_orders()

    plot = plot_types[plot_type]
    fig = plot(
        data,
        r="prob",
        theta="hour",
        row_facet=row_facet,
        col_facet=col_facet,
        showlegend=False,
        opacity=opacity / 100.0,
        **plot_type_kwargs[plot_type],
        category_orders=category_orders,
        radialaxis=dict(
            range=[0, 1],
            showticklabels=True,
            # title="Confidence",
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=(angles := list(range(0, 360, 45))),
            ticktext=[f"{int(angle / 360 * 24):02d}:00" for angle in angles],
            direction="clockwise",
            # title="Hour of Day",
            rotation=90,
            ticks=""
        )
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin=dict(r=150),
    )

    return fig

