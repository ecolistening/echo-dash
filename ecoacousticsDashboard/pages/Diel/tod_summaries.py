# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, dcc, callback, Output, Input, State, ALL
from loguru import logger

from utils.data import load_and_filter_dataset
from utils.modal_sound_sample import get_modal_sound_sample
from utils.save_plot_fig import get_save_plot

PAGENAME = 'tod-summaries'
PAGETITLE = 'Bar Plot of Descriptor by Time of Day'
dash.register_page(__name__, title=PAGETITLE, name='Bar Plot')

colours = {
    'main': 'blue',
    'accent1': 'red'
}

colours_tickbox = dmc.Chip('Colour by Recorder', value='colour', checked=True, persistence=True, id='colour-locations')
outliers_tickbox = dmc.Chip('Outliers', value='outlier', checked=True, persistence=True, id='outliers-tickbox')
separate_plots_tickbox = dmc.Chip('Plot per Recorder', value='subplots', checked=False, persistence=True,
                                  id='separate-plots')

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

appendix = dmc.Grid(
    children=[
        dmc.Col(html.Div([
            dmc.Title("Feature Name", order=3),
            dmc.Text('Feature Description')
                #'The Acoustic Evenness Index (AEI), from Villanueva-Rivera et al. 2011 (band evenness using the Gini index), is calculated by dividing the spectrogram into bins (default 10, each one of 1000 Hz) and taking the proportion of the signals in each bin above a threshold (default -50 dBFS). The AEI is the result of the Gini index applied to these bins.')
        ]), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

layout = html.Div([
    html.Div(
        [html.H1(PAGETITLE)],
    ),
    html.Hr(),
    dmc.Group(children=[
        time_aggregation,
        colours_tickbox,
        outliers_tickbox,
        separate_plots_tickbox
    ]),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    get_modal_sound_sample(PAGENAME),
    drilldown_file_div := html.Div(),
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input('feature-dropdown', component_property='value'),
    Input(time_aggregation, component_property='value'),
    Input(outliers_tickbox, component_property='checked'),
    Input(colours_tickbox, component_property='checked'),
    Input(separate_plots_tickbox, component_property='checked'),
)
def update_graph(dataset, dates, locations, feature, time_agg, outliers, colour_locations, separate_plots):
    logger.debug(f"Trigger Callback: {dataset=} {dates=} {locations=} {feature=} {time_agg=} {outliers=} {colour_locations=} {separate_plots=}")
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.sort_values(by='recorder')
    data = data.assign(time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0, hour=data.timestamp.dt.hour,
                       minute=data.timestamp.dt.minute)

    category_orders = {
        'time': None,
        'hour': None,
        'dddn': {'dddn': ['dawn', 'day', 'dusk', 'night']}
    }

    fig = px.box(data, x=time_agg, y='value',
                 hover_name='file', hover_data=['file', 'timestamp', 'path'], # Path last for sound sample modal
                 height=550,
                 facet_col='recorder' if separate_plots else None,
                 facet_col_wrap=4,
                 points='outliers' if outliers else False,
                 color='recorder' if colour_locations else None,
                 category_orders=category_orders[time_agg])

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(title={'text':f"{PAGETITLE} ({feature})",
                             'x':0.5,
                             'y':0.93,
                             'font':{'size':24}
                             })

    return fig