import dash
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, Input, State, ALL
from loguru import logger
from typing import List

from utils.content import get_tabs
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.save_plot_fig import get_save_plot

import components

PAGE_NAME = 'scatter-plot'
PAGE_TITLE = 'Scatter Plot of Descriptor by Time of Day'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Scatter Plot'
)

PLOTHEIGHT = 800

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
feature_select_id = "feature-dropdown"
graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-select"
symbol_select_id = f"{PAGE_NAME}-symbol-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
size_slider_id = f'{PAGE_NAME}-plot-size'

layout = html.Div([
    html.Div(
        [html.H1(PAGE_TITLE)],
    ),
    html.Hr(),
    dmc.Group(
        children=[
            components.ColourSelect(
                id=colour_select_id,
                default="month",
                categorical=True,
            ),
            components.SymbolSelect(
                id=symbol_select_id,
                default=None,
            ),
            components.RowFacetSelect(
                id=row_facet_select_id,
                default="sitelevel_1",
            ),
            components.ColumnFacetSelect(
                id=col_facet_select_id,
                default=None,
            ),
            components.SizeSlider(
                id=size_slider_id,
                default=3,
            )
        ],
        grow=True
    ),
    dmc.Divider(variant='dotted'),
    dcc.Graph(id=graph_id),
    components.Footer(
        PAGE_NAME,
    ),
    components.SoundSampleModal(
        PAGE_NAME,
    ),
    drilldown_file_div := html.Div(),
])

@callback(
    Output(graph_id, "figure"),
    State(dataset_select_id, "value"),
    Input(date_picker_id, component_property='value'),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(feature_select_id, "value"),
    Input(colour_select_id, "value"),
    Input(symbol_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(size_slider_id, "value"),
)
def update_figure(
    dataset_name,
    dates,
    locations,
    feature,
    colour_by,
    symbol_by,
    row_facet,
    col_facet,
    dot_size
) -> go.Figure:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: {dataset_name=} "
        f"dates:{len(dates)} locations:{len(locations)} "
        f"{feature=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=}"
    )

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.acoustic_features, dates=dates, locations=locations, feature=feature)

    data = data.assign(month=data.timestamp.dt.month, hour=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0,
                       minute=data.timestamp.dt.minute)

    fig = px.scatter(
        data,
        x='hour',
        y='value',
        hover_name='file',
        hover_data=['timestamp', 'path'], # Path last for sound sample modal
        height=PLOTHEIGHT,
        opacity=0.5,
        color=colour_by,
        symbol=symbol_by,
        facet_row=row_facet,
        facet_col=col_facet,
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

    # Adjust size of scatter dots
    fig.update_traces(marker=dict(size=dot_size))

    return fig
