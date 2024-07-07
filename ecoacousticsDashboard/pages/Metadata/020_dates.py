# Import packages

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import html, ctx, dcc, callback, Output, Input, State, ALL
from loguru import logger
from plotly_calplot import calplot

from utils.content import get_tabs
from utils.data import load_and_filter_dataset
from utils.save_plot_fig import get_save_plot

PAGENAME = 'dates'
PAGETITLE = 'Recording Dates'
PLOTHEIGHT = 800
dash.register_page(__name__, title=PAGETITLE, name='Dates')
#
# df = pd.read_parquet(filepath)
# df = df.assign(date=pd.to_datetime(df.timestamp.dt.date))

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
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    # Input('checklist-locations-hierarchy', component_property='value'),
    # Input('checklist-locations', component_property='value'),

    # Feature is not required, but helps with caching the dataset
    State('feature-dropdown', component_property='value'),
)
def update_graph(dataset, dates, locations, feature):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset=} dates:{len(dates)} locations:{len(locations)} {feature=}")

    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(date=pd.to_datetime(data.timestamp.dt.date))

    data = data.groupby('date').agg('count').reset_index()

    fig = calplot(data, x='date', y='file')

    # Add centered title
    fig.update_layout(
        height=PLOTHEIGHT,
        title={'text':'Recording Dates',
                             'x':0.5,
                             'y':1.0,
                             'font':{'size':24}
                             })

    return fig