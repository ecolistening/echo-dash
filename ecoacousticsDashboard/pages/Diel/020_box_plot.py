import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, Input, State, ALL
from loguru import logger
from typing import List

from utils.content import get_tabs
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.modal_sound_sample import get_modal_sound_sample
from utils.save_plot_fig import get_save_plot

import components

PAGE_NAME = "box-plot"
PAGE_TITLE = "Box Plot of Acoustic Descriptor by Time of Day"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Box Plot"
)

PLOT_HEIGHT = 800

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
feature_select_id = "feature-dropdown"
graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
time_aggregation_id = f"{PAGE_NAME}-time-aggregation"
outliers_tickbox_id = "outliers-tickbox"

layout = html.Div([
    html.Div(
        [html.H1(PAGE_TITLE)],
    ),
    html.Hr(),
    dmc.Group(children=[
        components.ColourSelect(
            id=colour_select_id,
            default="recorder",
            categorical=True,
        ),
        components.RowFacetSelect(
            id=row_facet_select_id,
            default=None,
        ),
        components.ColumnFacetSelect(
            id=col_facet_select_id,
            default=None,
        ),
        dmc.SegmentedControl(
            id=time_aggregation_id,
            data=[
                {"value": "time", "label": "15 minutes"},
                {"value": "hour", "label": "1 hour"},
                {"value": "dddn", "label": "Dawn-Day-Dusk-Night"}
            ],
            value="dddn",
            persistence=True
        ),
        dmc.Chip(
            "Outliers",
            id=outliers_tickbox_id,
            value="outlier",
            checked=True,
            persistence=True,
        )
    ]),
    dcc.Graph(id=graph_id),
    dmc.Grid(
        children=[
            dmc.Col(get_tabs(PAGE_NAME), span=8),
            dmc.Col(get_save_plot(graph_id), span=4),
        ],
        gutter="xl",
    ),
    components.SoundSampleModal(
        PAGE_NAME,
    ),
    drilldown_file_div := html.Div(),
])

@callback(
    Output(graph_id, "figure"),
    State(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(feature_select_id, "value"),
    Input(colour_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(time_aggregation_id, "value"),
    Input(outliers_tickbox_id, "checked"),
)
def update_graph(
    dataset_name: str,
    dates: List,
    locations: List,
    feature: str,
    colour_by: str,
    row_facet: str,
    col_facet: str,
    time_agg: str,
    outliers: bool,
) -> go.Figure:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: {dataset_name=} "
        f"dates:{len(dates)} locations:{len(locations)} "
        f"{feature=} {colour_by=} {row_facet=} {col_facet=} {time_agg=} {outliers=}"
    )

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.acoustic_features, dates=dates, locations=locations, feature=feature)

    data = data.sort_values(by='recorder')
    data = data.assign(time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0, hour=data.timestamp.dt.hour,
                       minute=data.timestamp.dt.minute)

    fig = px.box(
        data,
        x=time_agg,
        y='value',
        hover_name='file',
        hover_data=['file', 'timestamp', 'path'], # Path last for sound sample modal
        height=PLOT_HEIGHT,
        color=colour_by,
        facet_row=row_facet,
        facet_col=col_facet,
        facet_col_wrap=4,
        points='outliers' if outliers else False,
        category_orders=DatasetDecorator(dataset).category_orders()
    )

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(
        title={
            'text':f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    return fig
