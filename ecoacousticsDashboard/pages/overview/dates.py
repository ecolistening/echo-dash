# Import packages
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input, ALL
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from config import filepath, is_docker
from utils import load_and_filter_dataset

dash.register_page(__name__)
#
# df = pd.read_parquet(filepath)
# df = df.assign(date=pd.to_datetime(df.timestamp.dt.date))

layout = html.Div([
    html.Div(
        [dmc.Title('Recording Dates', order=1)],
    ),
    dmc.Divider(variant='dotted'),
    main_plot := dcc.Graph(id='dates-graph')
])

# Add controls to build the interaction
@callback(
    Output(main_plot, component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    # Input('checklist-locations-hierarchy', component_property='value'),
    # Input('checklist-locations', component_property='value'),
    Input('feature-dropdown', component_property='value'),
)
def update_graph(dataset, dates, locations, feature):
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(date=pd.to_datetime(data.timestamp.dt.date))

    data = data.groupby('date').agg('count').reset_index()

    fig = calplot(data, x='date', y='file')

    return fig