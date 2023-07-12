# Import packages
import json
from datetime import date
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, Patch
import dash_daq as daq
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from config import filepath, is_docker
from utils import load_and_filter_dataset

dash.register_page(__name__, title='Summaries', name='Summaries')

colours = {
    'main': 'blue',
    'accent1': 'red'
}

# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
# df = pd.read_parquet(filepath).drop_duplicates()
# df = df.assign(time=df.timestamp.dt.hour + df.timestamp.dt.minute / 60.0, hour=df.timestamp.dt.hour, minute=df.timestamp.dt.minute)#.astype('datetime64[ns]')

colours_tickbox = dmc.Chip('Colour by Recorder', value='colour', checked=True, persistence=True, id='colour-locations')
outliers_tickbox = dmc.Chip('Outliers', value='outlier', checked=True, persistence=True, id='outliers-tickbox')
separate_plots_tickbox = dmc.Chip('Plot per Recorder', value='subplots', checked=False, persistence=True, id='separate-plots')

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
    html.Div(
        [html.H1('Feature Summaries by Time of Day')],
    ),
    html.Hr(),
    dmc.Group(children=[
        time_aggregation,
        colours_tickbox,
        outliers_tickbox,
        separate_plots_tickbox
    ]),
    html.Div(
        main_plot := dcc.Graph(),
    ),
    html.Div([
        dmc.Title('Acoustic Evenness Index', order=3),
        dmc.Text('The Acoustic Evenness Index (AEI), from Villanueva-Rivera et al. 2011 (band evenness using the Gini index), is calculated by dividing the spectrogram into bins (default 10, each one of 1000 Hz) and taking the proportion of the signals in each bin above a threshold (default -50 dBFS). The AEI is the result of the Gini index applied to these bins.')
    ]),
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
    Input(time_aggregation, component_property='value'),
    Input(outliers_tickbox, component_property='checked'),
    Input(colours_tickbox, component_property='checked'),
    Input(separate_plots_tickbox, component_property='checked'),
)
def update_graph(dataset, dates, locations, recorders, feature, time_agg, outliers, colour_locations, separate_plots):
    data = load_and_filter_dataset(dataset, dates, feature, locations, recorders)
    data = data.sort_values(by='recorder')
    data = data.assign(time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0, hour=data.timestamp.dt.hour,
                   minute=data.timestamp.dt.minute)

    category_orders = {
        'time': None,
        'hour': None,
        'dddn': {'dddn': ['dawn','day','dusk','night']}
    }

    fig = px.box(data, x=time_agg, y='value',
                 hover_name='file', hover_data=['file', 'timestamp', 'timestamp'],
                 facet_col='recorder' if separate_plots else None,
                 facet_col_wrap=4,
                 points='outliers' if outliers else False,
                 color='recorder' if colour_locations else None,
                 category_orders=category_orders[time_agg])

    return fig

# @callback(
#     Output(drilldown_file_div, 'children'),
#     Input(main_plot, 'clickData'),
#     Input('feature-dropdown', 'value'))
# def display_click_data(clickData, value):
#     print(clickData)
#     if clickData is None:
#         return None
#     filename, ts, file_ts = clickData['points'][0]['customdata']
#
#     fig = px.line(data_frame=df[(df.timestamp == file_ts) & (df.feature == value)].sort_values(by='timestamp'), x='timestamp', y='value', color='recorder')
#     fig.update_xaxes(type='date')#, tickformat='%H:%M')
#
#     # Plot the feature curves
#     feature_plot = dcc.Graph(figure=fig)
#     return feature_plot