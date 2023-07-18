# Import packages
from pathlib import Path

import dash
from dash import Dash, html, dash_table, dcc, callback, Output, Input, ALL
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly_calplot import calplot

from config import filepath, is_docker, root_dir
from utils import load_and_filter_dataset

dash.register_page(__name__)

# df = pd.read_parquet(filepath)
# df = df.assign(date=pd.to_datetime(df.timestamp.dt.date))

layout = html.Div([
    html.Div(
        [dmc.Title('Location Map', order=1)],
    ),
    dmc.Divider(variant='dotted'),
    main_plot := dcc.Graph(id='map-overview-graph')
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
    # data = load_and_filter_dataset(dataset, dates, feature, locations)
    # data = data.assign(date=pd.to_datetime(data.timestamp.dt.date))
    #
    # data = data.groupby('date').agg('count').reset_index()
    #
    # fig = calplot(data, x='date', y='file')
    try:
        data = pd.read_parquet(root_dir / dataset / 'locations.parquet')
    except FileNotFoundError as e:
        return go.Figure(go.Scattergeo())

    extents = data.describe()

    fig = px.scatter_mapbox(data, lat="latitude", lon="longitude", hover_name="site",
                            hover_data=['timezone'],
                            # color_discrete_sequence=["fuchsia"],
                            zoom=1, height=500)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # fig.update_layout(mapbox_bounds={
    #     "west": extents.loc['min', 'longitude'],
    #     "east": extents.loc['max', 'longitude'],
    #     "south": extents.loc['min', 'latitude'],
    #     "north": extents.loc['max', 'latitude']
    # })
    # fig.show()
    # fig.update_geos(fitbounds='locations')

    return fig