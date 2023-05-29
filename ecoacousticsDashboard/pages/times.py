# Import packages
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from utils import is_docker

dash.register_page(__name__)

# Incorporate data
f = Path('/data/features.23D17.dashboard_subset_mini.parquet')
if not is_docker():
    f = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_subset_mini.parquet')

df = pd.read_parquet(f, columns=['file','file_timestamp','recorder']).drop_duplicates()
df = df.assign(date=pd.to_datetime(df.file_timestamp.dt.date), hour=df.file_timestamp.dt.hour + df.file_timestamp.dt.minute / 60.0)

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
    dcc.Checklist(options=df.recorder.unique(), inline=True, id='recorders-checkbox'),
    # dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='my-final-radio-item-example'),
    # dash_table.DataTable(data=df.to_dict('records'), page_size=6),
    dcc.Graph(id='times-graph')
])

# Add controls to build the interaction
@callback(
    Output(component_id='times-graph', component_property='figure'),
    Input(component_id='recorders-checkbox', component_property='value')
)
def update_graph(recs):
    data = df
    if recs is not None:
        data = df[df.recorder.isin(recs)]
    fig = px.scatter(data, x='date', y='hour', symbol='recorder', hover_name='file', opacity=0.5)
    fig.update_xaxes(type='category')
    fig.update_layout(scattermode="group", scattergap=0.75)
    return fig