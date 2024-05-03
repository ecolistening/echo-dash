# Import packages

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import html, dcc, callback, Output, Input, State, ALL
from loguru import logger
from plotly_calplot import calplot

from utils.data import load_and_filter_dataset

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

    # Feature is not required, but helps with caching the dataset
    State('feature-dropdown', component_property='value'),
)
def update_graph(dataset, dates, locations, feature):
    logger.debug(f"Trigger Callback: {dataset=} {dates=} {locations=} {feature=}")
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(date=pd.to_datetime(data.timestamp.dt.date))

    data = data.groupby('date').agg('count').reset_index()

    fig = calplot(data, x='date', y='file')

    # Add centered title
    fig.update_layout(title={'text':'Recording Dates',
                             'x':0.5,
                             'y':1.0,
                             'font':{'size':24}
                             })

    return fig