# Import packages
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from config import filepath
from utils import is_docker

dash.register_page(__name__)

df = pd.read_parquet(filepath, columns=['file','timestamp']).drop_duplicates()
df = df.assign(date=pd.to_datetime(df.timestamp.dt.date))
df = df.groupby('date').agg('count').reset_index()

layout = html.Div([
    html.Div(
        [html.H1('Recording Dates')],
    ),
    html.Hr(),
    # dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='my-final-radio-item-example'),
    # dash_table.DataTable(data=df.to_dict('records'), page_size=6),
    dcc.Graph(figure=calplot(df, x='date', y='file'), id='dates-graph')
])

# Add controls to build the interaction
# @callback(
#     Output(component_id='dates-graph', component_property='figure'),
#     Input(component_id='my-final-radio-item-example', component_property='value')
# )
# def update_graph(col_chosen):
#     fig = calplot(df, x='date', y='file')
#     return fig

# # Run the app
# if __name__ == '__main__':
#     app.run_server(host='0.0.0.0', debug=True)