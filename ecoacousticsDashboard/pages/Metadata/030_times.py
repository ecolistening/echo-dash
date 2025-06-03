# Import packages

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import html, ctx, dcc, callback, Output, Input, State, ALL
from loguru import logger

from utils.content import get_tabs
from utils.data import dataset_loader, filter_data, get_categorical_orders_for_dataset
from utils.modal_sound_sample import get_modal_sound_sample
from utils.plot_filter_menu import get_filter_drop_down, get_size_slider
from utils.save_plot_fig import get_save_plot

PAGENAME = 'times'
PAGETITLE = 'Recording Times'
PLOTHEIGHT = 800
dash.register_page(__name__, title=PAGETITLE, name='Times')

colour_select, symbol_select, row_facet_select, col_facet_select = get_filter_drop_down(PAGENAME, colour_default='location')
size_slider_text, size_slider = get_size_slider(PAGENAME)

filter_group = dmc.Group(children=[colour_select,symbol_select,row_facet_select,col_facet_select,size_slider_text,size_slider,dmc.Text()],grow=True)

appendix = dmc.Grid(
    children=[
        dmc.Col(get_tabs(PAGENAME,feature=False), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

# App layout
# app.\
layout = html.Div([
    html.Div(
        [html.H1(PAGETITLE)],
    ),
    html.Hr(),
    filter_group,
    dmc.Divider(variant='dotted'),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    get_modal_sound_sample(PAGENAME),
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),

    # Covered by menu filter
    State('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),

    # Feature is not required, but helps with caching the dataset
    State('feature-dropdown', component_property='value'),

    Input(colour_select, component_property='value'),
    Input(symbol_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(size_slider, component_property='value'),

    prevent_initial_call=True,
)
def update_graph(dataset, dates, locations, feature, colour_by, symbol_by, row_facet, col_facet, dot_size):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset=} dates:{len(dates)} locations:{len(locations)} {feature=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=}")

    data = data_loader.get_acoustic_features(dataset)
    data = filter_data(data, dates=dates, locations=locations, feature=feature)

    data = data.assign(date=data.timestamp.dt.date,
                       hour=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0)

    category_orders = get_categorical_orders_for_dataset(dataset)

    fig = px.scatter(data, x='date', y='hour', opacity=0.25,
                     height=PLOTHEIGHT,
                     hover_name='file', hover_data=['path'], # Path last for sound sample modal
                     color=colour_by,
                     symbol=symbol_by,
                     facet_row=row_facet,
                     facet_col=col_facet,
                     category_orders=category_orders,) 
    fig.update_layout(scattermode="group", scattergap=0.75)

    # Add centered title
    fig.update_layout(title={'text':'Recording Times',
                             'x':0.5,
                             'y':0.97,
                             'font':{'size':24}
                             })

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Adjust size of scatter dots
    fig.update_traces(marker=dict(size=dot_size))

    return fig
