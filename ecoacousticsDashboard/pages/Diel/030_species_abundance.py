import dash
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger
from typing import Any, Dict, List

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils import sketch
from utils.content import get_tabs
from utils.save_plot_fig import get_save_plot

import components

PAGE_NAME = "species-abundance"
PAGE_TITLE = "Species Abundance by Time of Day"
MENU_NAME = "Species Abundance"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=MENU_NAME,
)

# TODO: configure based on number of categories
PLOT_HEIGHT = 800
DEFAULT_THRESHOLD = 0.5

# setup data
dataset = dataset_loader.get_dataset(ds)

# setup plot type selector
plot_types = {
    "Scatter": px.scatter,
    "Scatter Polar": sketch.scatter_polar,
    "Bar Polar": sketch.bar_polar,
}
plot_type_kwargs = {
    "Scatter": dict(
        x='hour',
        y='richness',
        # hover_name="file",
        # hover_data=["timestamp", "path"],
    ),
    "Scatter Polar": dict(
        r="abundance",
        theta="hour",
        mode="markers",
        marker=dict(size=6, opacity=1.0),
        fill="toself",
        showlegend=False,
        radialaxis=dict(
            showticklabels=True,
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=(angles := list(range(0, 360, 45))),
            ticktext=[f"{int(angle / 360 * 24):02d}:00" for angle in angles],
            direction="clockwise",
            rotation=90,
            ticks=""
        )
    ),
    "Bar Polar": dict(
        r="abundance",
        theta="hour",
        marker_line_width=2,
        opacity=0.8,
        showlegend=False,
        radialaxis=dict(
            showticklabels=True,
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=(angles := list(range(0, 360, 45))),
            ticktext=[f"{int(angle / 360 * 24):02d}:00" for angle in angles],
            direction="clockwise",
            rotation=90,
            ticks=""
        )
    ),
}

# page selectors
dataset_select_id = "dataset-select"
graph_id = f"{PAGE_NAME}-graph"
plot_type_select_id = f"{PAGE_NAME}-plot-type-select"
species_select_id = f"{PAGE_NAME}-species-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
threshold_slider_id = f"{PAGE_NAME}-threshold-slider"

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
                value=None,
                data=[],
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
                "Threshold",
                size="sm",
                align="right",
            ),
            dmc.Slider(
                id=threshold_slider_id,
                min=0.1, max=0.9,
                step=0.1,
                value=DEFAULT_THRESHOLD,
                marks=[
                    dict(value=i, label=np.format_float_positional(i, precision=1))
                    for i in np.arange(0.1, 0.9, 0.1)
                ],
                persistence=True,
            ),
        ],
    ),
    dcc.Graph(id=graph_id),
    components.Footer(PAGE_NAME, feature=False),
])

@callback(
    Output(species_select_id, "value"),
    Output(species_select_id, "data"),
    Input(dataset_select_id, "value"),
    Input(threshold_slider_id, "value"),
    Input(species_select_id, "value"),
)
def update_species_select(
    dataset_name: str,
    threshold: float,
    current_species_name: str
) -> List[Dict[str, str]]:
    dataset = dataset_loader.get_dataset(dataset_name)
    scoped_species = sorted(dataset.species_predictions[dataset.species_predictions["confidence"] > threshold].common_name.unique())
    species_options = [dict(value=common_name, label=common_name) for common_name in scoped_species]
    if len(scoped_species) and current_species_name is None:
        current_species_name = scoped_species[0]
    return current_species_name, species_options

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(plot_type_select_id, "value"),
    Input(species_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(threshold_slider_id, "value"),
    prevent_initial_call=True,
)
def update_figure(
    dataset_name: str,
    locations,
    plot_type: str,
    species_name: str,
    row_facet: str,
    col_facet: str,
    threshold: float
) -> go.Figure:
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {species_name=} {plot_type=} {row_facet=} {col_facet=} {threshold=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = dataset.views.species_abundance(
        species_name=species_name,
        threshold=threshold,
        group_by=["hour", row_facet, col_facet, "site"],
    )
    data = filter_data(data, locations=locations)
    category_orders = DatasetDecorator(dataset).category_orders()
    plot = plot_types[plot_type]
    plot_kwargs = plot_type_kwargs[plot_type]
    fig = plot(
        data,
        **plot_kwargs,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=category_orders,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin=dict(r=150),
    )

    return fig

