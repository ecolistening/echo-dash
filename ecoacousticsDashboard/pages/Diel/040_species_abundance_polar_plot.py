import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.plot_filter_menu import get_filter_drop_down
from utils import sketch

PAGE_NAME = "species-abundance-polar-plot"
PAGE_TITLE = "Polar Plot of Species Abundance by Time of Day"
MENU_NAME = "Polar Species Abundance by Time of Day"
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

threshold_slider_text = dmc.Text("Detection Threshold", size="sm", align="right")
threshold_slider = dmc.Slider(
    id=f"{PAGE_NAME}-plot-size",
    min=0.1, max=1.0,
    step=0.1,
    value=0.5,
    marks=[
        { "value": i, "label": str(i) }
        for i in [0.1, 0.2, 0.4, 0.6, 0.8 , 0.1]
    ],
    persistence=True
)

filter_group = dmc.Group(children=[plot_type_select, colour_select, row_facet_select, col_facet_select, threshold_slider_text, threshold_slider], grow=True)

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
    Input(plot_type_select, "value"),
    Input(threshold_slider, "value"),
)
def update_figure(dataset_name, locations, colour_by, row_facet, col_facet, plot_type, threshold):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=}")

    dataset = dataset_loader.get_dataset(dataset_name)
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
            title="Call Count",
            ticks="",
        ),
        angularaxis=dict(
            tickmode="array",
            tickvals=[0, 90, 180, 270],
            ticktext=["00:00", "06:00", "12:00", "18:00"],
            direction="clockwise",
            # title="Hour of Day",
            rotation=90,
            ticks=""
        )
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        margin=dict(t=150, r=150),
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24)
        ),
    )

    return fig

