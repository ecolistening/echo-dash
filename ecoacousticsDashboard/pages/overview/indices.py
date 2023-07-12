# Import packages
import json
from datetime import date
from pathlib import Path

import dash
import dash_mantine_components as dmc
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, Patch
import pandas as pd
import plotly.express as px

from config import filepath, is_docker
from utils import load_and_filter_dataset

dash.register_page(__name__, title='Index Distributions', name='Index Distributions')

# df = pd.read_parquet(filepath).drop_duplicates()

# colours_tickbox = dmc.Chip('Colour by Recorder', value='colour', checked=True, persistence=True, id='colour-locations')
normalised_tickbox = dmc.Chip('Normalised', value='normalised', checked=False, persistence=True, id='normalised-tickbox')
diel_tickbox = dmc.Chip('Plot per Time of Day', value='diel', checked=False, persistence=True, id='separate-tod')
separate_plots_tickbox = dmc.Chip('Plot per Location', value='location', checked=False, persistence=True, id='separate-plots')

time_aggregation = dmc.SegmentedControl(
    id='time-aggregation',
    data=[
            {'value': 'time', 'label': '15 minutes'},
            {'value': 'hour', 'label': '1 hour'},
            {'value': 'dddn', 'label': 'Dawn-Day-Dusk-Night'}
    ],
    value='time',
    persistence=True
)

layout = html.Div([
    dmc.Title('Acoustic Index Distributions', order=1),
    dmc.Divider(variant='dotted'),
    dmc.Group(children=[
        # time_aggregation,
        # colours_tickbox,
        # outliers_tickbox,
        normalised_tickbox,
        diel_tickbox,
        separate_plots_tickbox
    ]),
    html.Div(
        main_plot := dcc.Graph(),
    ),
    drilldown_file_div := html.Div(),
])

# Add controls to build the interaction
@callback(
    Output(main_plot, component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input('checklist-locations-hierarchy', component_property='value'),
    Input('checklist-locations', component_property='value'),
    Input('feature-dropdown', component_property='value'),
    # Input(time_aggregation, component_property='value'),
    Input(normalised_tickbox, component_property='checked'),
    # Input(colours_tickbox, component_property='checked'),
    Input(diel_tickbox, component_property='checked'),
    Input(separate_plots_tickbox, component_property='checked'),
)
def update_graph(dataset, dates, locations, recorders, feature, normalised, diel_plots, separate_plots):#, time_agg, outliers, colour_locations, ):
    data = load_and_filter_dataset(dataset, dates, feature, locations, recorders)
    data = data.sort_values(by='recorder')

    fig = px.histogram(data, x='value', color='location', marginal='rug',# category_orders={'habitat code': ['EC1','EC2','EC3','UK1','UK2','UK3']},
                       facet_col='dddn' if diel_plots else None,
                       facet_row='location' if separate_plots else None,
                       histnorm='percent' if normalised else None,
                       category_orders={'dddn': ['dawn','day','dusk','night']}
                       )
    fig.update_traces(opacity=0.75)

    return fig