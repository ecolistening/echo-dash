# Import packages
from datetime import timedelta

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import html, dcc, callback, Output, Input

from utils import load_and_filter_dataset

dash.register_page(__name__, title='Index Averages', name='Index Averages')

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
        [html.H1('Seasonal Index Averages')],
    ),
    html.Hr(),
    # dmc.Group(children=[
    #     time_aggregation,
    #     colours_tickbox,
    #     outliers_tickbox,
    #     separate_plots_tickbox
    # ]),
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
    # Input(outliers_tickbox, component_property='checked'),
    # Input(colours_tickbox, component_property='checked'),
    # Input(separate_plots_tickbox, component_property='checked'),
)
def update_graph(dataset, dates, locations, recorders, feature):#, time_agg, outliers, colour_locations, separate_plots):
    data = load_and_filter_dataset(dataset, dates, feature, locations, recorders)
    data = data.sort_values(by='recorder')
    data = data.assign(time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0, hour=data.timestamp.dt.hour,
                   minute=data.timestamp.dt.minute)

    category_orders = {
        'time': None,
        'hour': None,
        'dddn': {'dddn': ['dawn','day','dusk','night']}
    }

    data = data.sort_values('timestamp').\
        groupby(by=['location','recorder','feature','dddn']).\
        rolling(window=timedelta(days=7), center=True, on='timestamp').\
        agg({'value': ['mean', 'std']}).reset_index().\
        groupby(by=['location','recorder','feature','dddn', pd.Grouper(freq='1D', key='timestamp')]).mean().reset_index()

    data.columns = [list(filter(lambda x: x != '' and x != 'value', col))[0] for col in data.columns.values]

    fig = px.line(data, x='timestamp', y='mean', color='location', facet_row='dddn', markers=True)
    fig.update_traces(marker={'size': 4})

    # fig.add_trace(
    #     go.Scatter(
    #         x = data.timestamp,
    #         y = data['mean'] + data['std'],
    #         mode='lines'
    #     )
    # )

    fig.update_layout(height=800)

    return fig
