# Import packages
import json
from datetime import date
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, Patch
import dash_daq as daq
import pandas as pd
import plotly.express as px
from plotly_calplot import calplot

from utils import is_docker, filter_dataset

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
df = df.assign(time=df.timestamp.dt.hour + df.timestamp.dt.minute / 60.0, hour=df.timestamp.dt.hour, minute=df.timestamp.dt.minute)#.astype('datetime64[ns]')

# agg_by_selector = dbc.

outliers_tickbox = daq.BooleanSwitch(
    id='outliers-tickbox',
    label='Show Outliers',
    persistence=True,
    # labelPosition='left',
    # vertical=True
)

colours_tickbox = daq.BooleanSwitch(
    id='colour-locations',
    label='Colour Locations',
    persistence=True,
    # labelPosition='right',
    # vertical=True
)

separate_plots_tickbox = daq.BooleanSwitch(
    id='separate-plots',
    label='Separate Plots',
    persistence=True,
    on=True,
    # labelPosition='right',
    # vertical=True
)

time_aggregation = html.Div([
    dbc.Label("Time Aggregation", html_for="time-aggregation"),
    time_aggregation_selection := dcc.Dropdown(
        id='time-aggregation',
        options={
            'time': '15 minutes',
            'hour': '1 hour',
            'dddn': 'Dawn-Day-Dusk-Night'
        }, value=15,
        clearable=False, persistence=True),
])

layout = html.Div([
    html.Div(
        [html.H1('Feature Summaries by Time of Day')],
    ),
    html.Hr(),
    dbc.Form([
        time_aggregation,
        outliers_tickbox,
        colours_tickbox,
        separate_plots_tickbox
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
    Input('date-picker', component_property='start_date'),
    Input('date-picker', component_property='end_date'),
    Input('checklist-locations', component_property='value'),
    Input('feature-dropdown', component_property='value'),
    Input(time_aggregation_selection, component_property='value'),
    Input(outliers_tickbox, component_property='on'),
    Input(colours_tickbox, component_property='on'),
    Input(separate_plots_tickbox, component_property='on'),
)
def update_graph(start_date, end_date, locations, feature, time_agg, outliers, colour_locations, separate_plots):
    data = filter_dataset(df, [start_date, end_date], feature, locations)

    category_orders = {
        'time': None,
        'hour': None,
        'dddn': {'dddn': ['dawn','day','dusk','night']}
    }

    fig = px.box(data, x=time_agg, y='value',
                 hover_name='file', hover_data=['file', 'timestamp', 'file_timestamp'],
                 facet_col='recorder' if separate_plots == True else None,
                 points='outliers' if outliers == True else False,
                 color='recorder' if colour_locations == True else None,
                 category_orders=category_orders[time_agg])

    # fig.update_traces(marker={
    #     'color': colours['accent1'],
    #     'size': 4
    # },
    # line={
    #     'color': colours['main']
    # })

    return fig

@callback(
    Output(drilldown_file_div, 'children'),
    Input(main_plot, 'clickData'),
    Input('feature-dropdown', 'value'))
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