# Import packages
import json
from datetime import date
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from utils import is_docker

dash.register_page(__name__, title='Features by Time-of-Day', name='Features by Time-of-Day')

# Incorporate data
f = Path('/data/features.23D17.dashboard_subset_mini.parquet')
if not is_docker():
    f = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_subset_mini.parquet')

# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
df = pd.read_parquet(f).drop_duplicates()

df = df.assign(hour=df.timestamp.dt.hour + df.timestamp.dt.minute / 60.0, minute=df.timestamp.dt.minute)#.astype('datetime64[ns]')
# df.time = pd.Timestamp.combine(date(2000,1,1), df.time)
# print(df.dtypes)

# fig = px.scatter(df, x='date', y='hour', symbol='recorder', hover_name='file', opacity=0.5)
# fig.update_xaxes(type='category')
# fig.update_layout(scattermode="group", scattergap=0.75)

# App layout
# app.\
layout = html.Div([
    html.Div(
        [html.H1('Features by Time of Day')],
    ),
    html.Hr(),
    html.Div([
        html.Label('Feature: '),
        dcc.Dropdown(options=df.feature.unique(), value=df.feature.unique()[0], id='feature-checkbox'),
    ]),
    html.Div(
        dcc.Graph(id='tod-features-graph'),
    ),
    drilldown_file_div := html.Div(),
])

# Add controls to build the interaction
@callback(
    Output(component_id='tod-features-graph', component_property='figure'),
    Input(component_id='feature-checkbox', component_property='value'),
    Input(component_id='checklist-locations', component_property='value')
)
def update_graph(feature, locations):
    data = df[(df.feature == feature) & (df.recorder.isin(locations))]
    fig = px.scatter(data, x='hour', y='value', hover_name='file', hover_data=['file', 'timestamp', 'file_timestamp'], opacity=0.5, facet_col='recorder')
    # fig.update_xaxes(type='date', tickformat='%H:%M')
    return fig

@callback(
    Output(drilldown_file_div, 'children'),
    Input('tod-features-graph', 'clickData'),
    Input('feature-checkbox', 'value'))
def display_click_data(clickData, value):
    if clickData is None:
        return None
    filename, ts, file_ts = clickData['points'][0]['customdata']

    fig = px.line(data_frame=df[(df.file_timestamp == file_ts) & (df.feature == value)].sort_values(by='timestamp'), x='timestamp', y='value', color='recorder')
    fig.update_xaxes(type='date')#, tickformat='%H:%M')

    # Plot the feature curves
    feature_plot = dcc.Graph(figure=fig)
    return feature_plot