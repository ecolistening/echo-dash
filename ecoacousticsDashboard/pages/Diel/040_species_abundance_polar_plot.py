import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils import sketch

import components

PAGE_NAME = "species-abundance-polar-plot"
PAGE_TITLE = "Polar Plot of Species Abundance by Time of Day"
MENU_NAME = "Polar Species Abundance by Time of Day"

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
        mode="markers",
        marker=dict(size=6, opacity=1.0),
        fill="toself",
    ),
    "Bar Polar": dict(
        marker_line_width=2,
        opacity=0.8,
    ),
}

# page selectors
dataset_select_id = "dataset-select"
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
            components.RowFacetSelect(
                id=row_facet_select_id,
                default=None,
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
                default=None,
            ),
            dmc.Text(
                children="Detection Threshold",
                size="sm",
                align="right",
            ),
            dmc.Slider(
                id=threshold_slider_id,
                min=0.1, max=1.0,
                step=0.1,
                value=0.5,
                marks=[
                    { "value": i, "label": str(i) }
                    for i in [0.1, 0.2, 0.4, 0.6, 0.8 , 0.1]
                ],
                persistence=True,
            ),
        ],
        grow=True,
    ),
    dcc.Graph(id=graph_id),
])

@callback(
    Output(graph_id, "figure"),
    Input(dataset_select_id, "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(plot_type_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(threshold_slider_id, "value"),
)
def update_figure(
    dataset_name: str,
    locations,
    plot_type: str,
    row_facet: str,
    col_facet: str,
    threshold: float,
) -> go.Figure:
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {plot_type=} {row_facet=} {col_facet=} {threshold=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    import code; code.interact(local=locals())
    data = dataset.views.species_abundance_by_hour(threshold, row_facet, col_facet)
    data = filter_data(data, locations=locations)
    category_orders = DatasetDecorator(dataset).category_orders()

    plot = plot_types[plot_type]
    fig = plot(
        data,
        r="presence",
        theta="hour",
        row_facet=row_facet,
        col_facet=col_facet,
        showlegend=False,
        **plot_type_kwargs[plot_type],
        category_orders=category_orders,
        radialaxis=dict(
            showticklabels=True,
            # title="Call Count",
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
        margin=dict(t=150, r=150),
    )

    return fig
