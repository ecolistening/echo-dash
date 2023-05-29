# Import packages
import json
from datetime import date
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import dash_daq as daq
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from utils import is_docker

dash.register_page(__name__, title='Feature Summaries by Time-of-Day', name='Feature Summaries by Time-of-Day')

colours = {
    'main': 'blue',
    'accent1': 'red'
}

# Incorporate data
f = Path('/data/features.23D17.dashboard_subset_mini.parquet')
if not is_docker():
    f = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_subset_mini.parquet')

# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
df = pd.read_parquet(f).drop_duplicates()
df = df.assign(hour=df.timestamp.dt.hour + df.timestamp.dt.minute / 60.0, minute=df.timestamp.dt.minute)#.astype('datetime64[ns]')

layout = html.Div([
    html.Div(
        [html.H1('Feature Summaries by Time of Day')],
    ),
    html.Hr(),
    html.Div([
        html.Label('Feature: '),
        feature_checkbox := dcc.Dropdown(
            options=df.feature.unique(), value=df.feature.unique()[0],
            style={'min-width': '200px'}, clearable=False),
        outliers_tickbox := daq.ToggleSwitch(
            label='Show Outliers',
            labelPosition='left'
        )
    ],
        style={"display":"flex", "gap":"20px", "align-items":"flex-end"}
    ),
    html.Div(
        main_plot := dcc.Graph(),
    ),
    drilldown_file_div := html.Div(),
])

# Add controls to build the interaction
@callback(
    Output(main_plot, component_property='figure'),
    Input(feature_checkbox, component_property='value'),
    Input(component_id='checklist-locations', component_property='value')
)
def update_graph(feature, locations):
    data = df[(df.feature == feature) & (df.recorder.isin(locations))]
    fig = px.box(data, x='hour', y='value',
                 hover_name='file', hover_data=['file', 'timestamp', 'file_timestamp'],
                 facet_col='recorder', points='outliers')
    fig.update_traces(marker={
        'color': colours['accent1'],
        'size': 4
    },
    line={
        'color': colours['main']
    })
    # fig.update_xaxes(type='date', tickformat='%H:%M')
    return fig

@callback(
    Output(drilldown_file_div, 'children'),
    Input(main_plot, 'clickData'),
    Input(feature_checkbox, 'value'))
def display_click_data(clickData, value):
    print(clickData)
    if clickData is None:
        return None
    filename, ts, file_ts = clickData['points'][0]['customdata']

    fig = px.line(data_frame=df[(df.file_timestamp == file_ts) & (df.feature == value)].sort_values(by='timestamp'), x='timestamp', y='value', color='recorder')
    fig.update_xaxes(type='date')#, tickformat='%H:%M')

    # Plot the feature curves
    feature_plot = dcc.Graph(figure=fig)
    return feature_plot