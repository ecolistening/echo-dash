# Import packages
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from config import filepath
from utils import is_docker, filter_dataset

dash.register_page(__name__)

df = pd.read_parquet(filepath).drop_duplicates()
df = df.assign(date=pd.to_datetime(df.timestamp.dt.date), hour=df.timestamp.dt.hour + df.timestamp.dt.minute / 60.0)

# fig = px.scatter(df, x='date', y='hour', symbol='recorder', hover_name='file', opacity=0.5)
# fig.update_xaxes(type='category')
# fig.update_layout(scattermode="group", scattergap=0.75)

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
    dcc.Graph(id='times-graph')
])

# Add controls to build the interaction
@callback(
    Output(component_id='times-graph', component_property='figure'),
    Input('date-picker', component_property='value'),
    Input('checklist-locations-hierarchy', component_property='value'),
    Input('checklist-locations', component_property='value'),
    Input('feature-dropdown', component_property='value'),
)
def update_graph(dates, locations, recorders, feature):
    data = filter_dataset(df, dates, feature, locations, recorders)

    fig = px.scatter(data, x='date', y='hour', color='habitat code', hover_name='file', opacity=0.5)
    fig.update_xaxes(type='category')
    fig.update_layout(scattermode="group", scattergap=0.75)

    return fig