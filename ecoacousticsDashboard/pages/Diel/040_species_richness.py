import dash
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from datetime import date
from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger
from typing import Any, Dict, List

from menu.dataset import ds
from utils import list2tuple, dedup
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils import sketch
from utils.content import get_tabs
from utils.save_plot_fig import get_save_plot

import components

PAGE_NAME = "species-richness"
PAGE_TITLE = "Species Richness by Time of Day"
MENU_NAME = "Species Richness"

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
    "Scatter": sketch.scatter,
    "Scatter Polar": sketch.scatter_polar,
    "Bar Polar": sketch.bar_polar,
}
plot_type_kwargs = {
    "Scatter": dict(
        x='hour',
        y='richness',
        marker=dict(
            size=10,
            opacity=1.0,
            color="rgba(133, 143, 249, 1.0)",
        ),
    ),
    "Scatter Polar": dict(
        r="richness",
        theta="hour",
        mode="markers",
        marker=dict(
            size=10,
            opacity=1.0,
            color="rgba(133, 143, 249, 1.0)",
        ),
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
        r="richness",
        theta="hour",
        marker_line_width=2,
        opacity=0.8,
        showlegend=False,
        marker=dict(
            color="rgba(133, 143, 249, 0.6)",
            line=dict(color="rgba(133, 143, 249, 1.0)", width=2)
        ),
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
date_picker_id = "date-picker"
graph_id = f"{PAGE_NAME}-graph"
plot_type_select_id = f"{PAGE_NAME}-plot-type-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
threshold_slider_id = f"{PAGE_NAME}-threshold-slider"

# full layout
layout = html.Div([
    html.Div([
        html.H1(PAGE_TITLE),
    ]),
    html.Hr(),
    dmc.Divider(variant="dotted"),
    dmc.Group(
        children=[
            dmc.Select(
                id=plot_type_select_id,
                label="Select plot type",
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
            components.RowFacetSelect(
                id=row_facet_select_id,
                default=None,
                ignore_options=["hour"],
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
                default=None,
                ignore_options=["hour"],
            ),
            dmc.Text(
                children="Detection Threshold",
                size="sm",
                align="right",
            ),
            dmc.Slider(
                id=threshold_slider_id,
                min=0.1, max=0.9,
                step=0.1,
                value=0.5,
                marks=[
                    dict(value=i, label=np.format_float_positional(i, precision=1))
                    for i in np.arange(0.1, 0.9, 0.1)
                ],
                persistence=True,
            ),
        ],
        grow=True,
    ),
    dcc.Graph(id=graph_id),
    components.Footer(PAGE_NAME, feature=False),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(plot_type_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(threshold_slider_id, "value"),
)
def update_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    plot_type: str,
    row_facet: str,
    col_facet: str,
    threshold: float,
) -> go.Figure:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"{dataset_name=} dates={dates} locations={locations} "
        f"{plot_type=} {row_facet=} {col_facet=} {threshold=} "
    )

    group_by = list(filter(lambda x: x is not None, dedup(["hour", row_facet, col_facet])))
    dataset = dataset_loader.get_dataset(dataset_name)
    data = dataset.views.species_richness(
        threshold,
        group_by=group_by,
        dates=list2tuple(dates),
        locations=list2tuple(locations)
    )

    category_orders = DatasetDecorator(dataset).category_orders()

    plot = plot_types[plot_type]
    fig = plot(
        data,
        **plot_type_kwargs[plot_type],
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=category_orders,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin=dict(t=150, r=150),
    )

    return fig
