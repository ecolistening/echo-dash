# Import packages

import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, ctx, dcc, callback, Output, Input, ALL
from loguru import logger

from utils.content import get_tabs
from utils.data import dataset_loader
from utils.save_plot_fig import get_save_plot

PAGENAME = 'map'
PAGETITLE = 'Location Map'
PLOTHEIGHT = 800
dash.register_page(__name__, title=PAGETITLE, name='Map')

appendix = dmc.Grid(
    children=[
        dmc.Col(get_tabs(PAGENAME,feature=False), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

layout = html.Div([
    html.Div(
        [dmc.Title(PAGETITLE, order=1)],
    ),
    dmc.Divider(variant='dotted'),
    main_plot := dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
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
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset=} dates:{len(dates)} locations:{len(locations)} {feature=}")

    data = dataset_loader.get_sites(dataset)
    if data is None:
        return go.Figure(go.Scattergeo())


    '''
        Calculate Zoom Level for World Map

        https://docs.mapbox.com/help/glossary/zoom-level/#zoom-levels-and-geographical-distance
    '''
    extents = data.describe()
    longitude_range = extents.loc['max', 'longitude'] - extents.loc['min', 'longitude']
    latitude_range = extents.loc['max', 'latitude'] - extents.loc['min', 'latitude']

    # The 111 is a constant to convert decimal degrees to kilometers
    max_bound = max(longitude_range, latitude_range) * 111

    # Formula established by trial-and-error
    zoom = 12 - np.log(max_bound)*1.1

    logger.debug(f"{dataset=} {latitude_range=:.4f} {longitude_range=:.4f} {max_bound=:.4f} {np.log(max_bound)=:.4f} {zoom=:.4f}")

    fig = px.scatter_mapbox(data, lat="latitude", lon="longitude", hover_name="site",
                            hover_data=['timezone'],
                            color_discrete_sequence=["red"],
                            zoom=zoom, height=PLOTHEIGHT)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig
