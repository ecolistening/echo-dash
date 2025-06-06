import dash
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils import sketch
from utils.content import get_tabs
from utils.save_plot_fig import get_save_plot

import components

PAGE_NAME = "species-occurrence"
PAGE_TITLE = "Species Occurrence by Time of Day"
MENU_NAME = "Species Occurrence"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=MENU_NAME,
)

# TODO: configure based on number of categories
PLOT_HEIGHT = 800

# setup data
dataset = dataset_loader.get_dataset(ds)
species_list = sorted(dataset.species_predictions.common_name.unique())
species_default = species_list[0]

# setup plot type selector
plot_types = {
    "Scatter Polar": sketch.scatter_polar,
    "Bar Polar": sketch.bar_polar,
}
plot_type_kwargs = {
    "Scatter Polar": dict(
        r="prob",
        theta="hour",
        mode="markers",
        marker=dict(size=6, opacity=1.0),
        fill="toself",
    ),
    "Bar Polar": dict(
        r="prob",
        theta="hour",
        marker_line_width=2,
        opacity=0.8,
    ),
}

# page selectors
dataset_select_id = "dataset-select"
graph_id = f"{PAGE_NAME}-graph"
plot_type_select_id = f"{PAGE_NAME}-plot-type-select"
species_select_id = f"{PAGE_NAME}-species-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
opacity_slider_id = f'{PAGE_NAME}-opacity-slider'

# full layout
layout = html.Div([
    html.Div([
        html.H1(PAGE_TITLE)
    ]),
    html.Hr(),
    dmc.Divider(variant="dotted"),
    dmc.Group(
        grow=True,
        children=[
            dmc.Select(
                id=plot_type_select_id,
                label="Select polar plot type",
                value="Bar Polar",
                data=[
                    dict(value=plot_type, label=plot_type)
                    for plot_type in plot_types.keys()
                ],
                searchable=True,
                clearable=False,
                style=dict(width=200),
                persistence=True,
            ),
            dmc.Select(
                id=species_select_id,
                label="Select species",
                value=species_default,
                data=[
                    dict(value=common_name, label=common_name)
                    for common_name in species_list
                ],
                searchable=True,
                clearable=False,
                style=dict(width=200),
                persistence=True,
            ),
            components.RowFacetSelect(
                id=row_facet_select_id,
                default=None,
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
                default=None,
            ),
            dmc.Text(
                "Opacity",
                size="sm",
                align="right",
            ),
            dmc.Slider(
                id=opacity_slider_id,
                min=0, max=100, step=5, value=50,
                marks=[
                    dict(value=i, label=f',{i}%')
                    for i in range(0, 101, 20)
                ],
                persistence=True
            ),
        ],
    ),
    dcc.Graph(id=graph_id),
    components.Footer(PAGE_NAME, feature=False),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(plot_type_select_id, "value"),
    Input(species_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(opacity_slider_id, "value"),
)
def update_figure(
    dataset_name: str,
    locations,
    plot_type: str,
    species_name: str,
    row_facet: str,
    col_facet: str,
    opacity: float,
) -> go.Figure:
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {species_name=} {plot_type=} {row_facet=} {col_facet=} {opacity=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = dataset.views.species_probability(
        species_name=species_name,
        group_by=["hour", row_facet, col_facet],
    )
    data = filter_data(data, locations=locations)
    category_orders = DatasetDecorator(dataset).category_orders()

    plot = plot_types[plot_type]
    plot_kwargs = plot_type_kwargs[plot_type]
    plot_kwargs["opacity"] = opacity / 100.0
    fig = plot(
        data,
        **plot_kwargs,
        facet_row=row_facet,
        facet_col=col_facet,
        showlegend=False,
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

