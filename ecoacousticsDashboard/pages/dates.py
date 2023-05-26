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
f = Path('/data/features.23D17.dashboard_subset.parquet')
if not is_docker():
    f = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_subset.parquet')

df = pd.read_parquet(f, columns=['file','file_timestamp']).drop_duplicates()
df = df.assign(date=pd.to_datetime(df.file_timestamp.dt.date))
df = df.groupby('date').agg('count').reset_index()

layout = html.Div([
    html.Div(
        [html.H1('Recording Dates')],
    ),
    html.Hr(),
    # dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='my-final-radio-item-example'),
    dash_table.DataTable(data=df.to_dict('records'), page_size=6),
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