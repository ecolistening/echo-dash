# Import packages

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Output, Input, State, ALL
from loguru import logger

from utils.data import load_and_filter_dataset
from utils.modal_sound_sample import get_modal_sound_sample
from utils.save_plot_fig import get_save_plot

PAGENAME = 'Times'
dash.register_page(__name__, title=PAGENAME, name=PAGENAME)

appendix = dmc.Grid(
    children=[
        dmc.Col(html.Div(), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

# App layout
# app.\
layout = html.Div([
    html.Div(
        [html.H1('Recording Times')],
    ),
    html.Hr(),
    # dcc.Checklist(options=df.recorder.unique(), inline=True, id='recorders-checkbox'),
    # dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='my-final-radio-item-example'),
    # dash_table.DataTable(data=df.to_dict('records'), page_size=6),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    get_modal_sound_sample(PAGENAME),
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),

    # Feature is not required, but helps with caching the dataset
    State('feature-dropdown', component_property='value'),
)
def update_graph(dataset, dates, locations, feature):
    logger.debug(f"Trigger Callback: {dataset=} {dates=} {locations=} {feature=}")
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(date=data.timestamp.dt.date,
                       hour=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0)

    fig = px.scatter(data, x='date', y='hour', color='location', opacity=0.25, hover_name='file', hover_data=['path']) # Path last for sound sample modal
    fig.update_xaxes(type='category', categoryorder='category ascending')
    fig.update_layout(scattermode="group", scattergap=0.75)

    # Add centered title
    fig.update_layout(title={'text':'Recording Times',
                             'x':0.5,
                             'y':0.95,
                             'font':{'size':24}
                             })

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    return fig