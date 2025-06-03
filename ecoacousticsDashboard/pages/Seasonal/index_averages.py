# Import packages
from datetime import timedelta

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
import warnings
from dash import html, ctx, dcc, callback, Output, Input, ALL
from loguru import logger

from utils.content import get_tabs
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.save_plot_fig import get_save_plot

PAGENAME = 'idx-averages'
PAGETITLE = 'Seasonal Descriptor Averages'
PLOTHEIGHT = 800
dash.register_page(__name__, title=PAGETITLE, name='Averages')

# colours_tickbox = dmc.Chip('Colour by Recorder', value='colour', checked=True, persistence=True, id='colour-locations')
# outliers_tickbox = dmc.Chip('Outliers', value='outlier', checked=True, persistence=True, id='outliers-tickbox')
# separate_plots_tickbox = dmc.Chip('Plot per Recorder', value='subplots', checked=False, persistence=True,
#                                   id='separate-plots')

# time_aggregation = dmc.SegmentedControl(
#     id='time-aggregation',
#     data=[
#         {'value': 'time', 'label': '15 minutes'},
#         {'value': 'hour', 'label': '1 hour'},
#         {'value': 'dddn', 'label': 'Dawn-Day-Dusk-Night'}
#     ],
#     value='time',
#     persistence=True
# )

appendix = dmc.Grid(
    children=[
        dmc.Col(get_tabs(PAGENAME), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

layout = html.Div([
    html.Div(
        [html.H1(PAGETITLE)],
    ),
    html.Hr(),
    # dmc.Group(children=[
    #     time_aggregation,
    #     colours_tickbox,
    #     outliers_tickbox,
    #     separate_plots_tickbox
    # ]),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    drilldown_file_div := html.Div(),
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    # Input('checklist-locations-hierarchy', component_property='value'),
    # Input('checklist-locations', component_property='value'),
    Input('feature-dropdown', component_property='value'),
    # Input(time_aggregation, component_property='value'),
    # Input(outliers_tickbox, component_property='checked'),
    # Input(colours_tickbox, component_property='checked'),
    # Input(separate_plots_tickbox, component_property='checked'),
)
def update_graph(dataset_name, dates, locations, feature):  # , time_agg, outliers, colour_locations, separate_plots):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} dates:{len(dates)} locations:{len(locations)} {feature=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.acoustic_features, dates=dates, locations=locations, feature=feature)

    data = data.sort_values(by='recorder')
    data = data.assign(time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0, hour=data.timestamp.dt.hour,
                       minute=data.timestamp.dt.minute)

    # data = data.sort_values('timestamp'). \
    #     groupby(by=['location', 'recorder', 'feature', 'dddn']). \
    #     rolling(window=timedelta(days=7), center=True, on='timestamp'). \
    #     agg({'value': ['mean', 'std']}).reset_index(). \
    #     groupby(
    #     by=['location', 'recorder', 'feature', 'dddn', pd.Grouper(freq='1D', key='timestamp')]).mean().reset_index()

    data = data.sort_values('timestamp')
    data = data.groupby(by=['location', 'recorder', 'feature', 'dddn'])
    data = data.rolling(window=timedelta(days=7), center=True, on='timestamp')
    data = data.agg({'value': ['mean', 'std']}).reset_index()
    data = data.groupby(by=['location', 'recorder', 'feature', 'dddn', pd.Grouper(freq='1D', key='timestamp')])

    # Suppress Pandas Performance Warning
    with warnings.catch_warnings(action="ignore"):
        data = data.mean().reset_index()

    data.columns = [list(filter(lambda x: x != '' and x != 'value', col))[0] for col in data.columns.values]

    fig = px.line(data, x='timestamp', y='mean', color='location', facet_row='dddn', markers=True, category_orders=DatasetDecorator(dataset).category_orders())
    fig.update_traces(marker={'size': 4})

    # Add centered title
    fig.update_layout(height=PLOTHEIGHT,
                      title={'text':f"{PAGETITLE} ({feature})",
                             'x':0.5,
                             'y':0.98,
                             'font':{'size':24}
                             })

    return fig
