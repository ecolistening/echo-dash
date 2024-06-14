# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, dcc, callback, Output, Input, State, ALL, clientside_callback
from loguru import logger

from utils.data import load_and_filter_dataset, get_options_for_dataset
from utils.modal_sound_sample import get_modal_sound_sample
from utils.save_plot_fig import get_save_plot

PAGENAME = 'tod-features'
dash.register_page(__name__, title='Acoustic Indices', name='Acoustic Indices')

colour_select = dmc.Select(
    id=f'{PAGENAME}-plot-options-color-by',
    label="Colour by",
    value="month",
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
symbol_select = dmc.Select(
    id=f'{PAGENAME}-plot-options-symbol-by',
    label="Symbolise by",
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
row_facet_select = dmc.Select(
    id=f'{PAGENAME}-plot-options-rowfacet-by',
    label="Facet Rows by",
    value="sitelevel_1",
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
col_facet_select = dmc.Select(
    id=f'{PAGENAME}-plot-options-colfacet-by',
    label="Facet Columns by",
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)

size_slider = dmc.Slider(
    id=f'{PAGENAME}-plot-size',
    min=1, max=20, step=1, value=3,
    persistence=True
)

appendix = dmc.Grid(
    children=[
        dmc.Col(html.Div(), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

# App layout
# app.\
layout = html.Div([
    html.Div(
        [html.H1('Features by Time of Day')],
    ),
    html.Hr(),
    dmc.Group(children=[
        colour_select,
        symbol_select,
        row_facet_select,
        col_facet_select,
        dmc.Text('Dot Size', size='sm', align='right'),
        size_slider,
    ], grow=True),
    dmc.Divider(variant='dotted'),
    # dmc.Group([
    #     dmc.Text('Dot Size', size='sm', align='right'),
    #     size_slider,
    # ], grow=True),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    get_modal_sound_sample(PAGENAME),
    drilldown_file_div := html.Div(),
])


@callback(
    Output(colour_select, component_property='data'),
    Output(symbol_select, component_property='data'),
    Output(row_facet_select, component_property='data'),
    Output(col_facet_select, component_property='data'),

    Output(colour_select, component_property='value'),
    Output(symbol_select, component_property='value'),
    Output(row_facet_select, component_property='value'),
    Output(col_facet_select, component_property='value'),

    Input('dataset-select', component_property='value'),

    State(colour_select, component_property='value'),
    State(symbol_select, component_property='value'),
    State(row_facet_select, component_property='value'),
    State(col_facet_select, component_property='value'),
)
def update_options(dataset, colour_by, symbol_by, row_facet, col_facet,):
    logger.debug(f"Trigger Callback: {dataset=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=}")
    
    all_options = get_options_for_dataset(dataset)

    # Select only categorical options
    cat_options = [opt for opt in all_options if opt['type'] in ('categorical')]

    # Ensure option is available for dataset
    val_all_options = [opt['value'] for opt in all_options]
    val_cat_options = [opt['value'] for opt in cat_options]

    if colour_by not in val_all_options: colour_by = None
    if symbol_by not in val_cat_options: symbol_by = None
    if row_facet not in val_cat_options: row_facet = None
    if col_facet not in val_cat_options: col_facet = None

    return all_options, cat_options, cat_options, cat_options, colour_by, symbol_by, row_facet, col_facet


@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),
    Input(colour_select, component_property='data'),

    Input(colour_select, component_property='value'),
    Input(symbol_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(size_slider, component_property='value'),

    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input('feature-dropdown', component_property='value'),

    State('dataset-select', component_property='value'),
    prevent_initial_call=True,
)
def load_fig(options, colour_by, symbol_by, row_facet, col_facet, dot_size, dates, locations, feature, dataset):
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(month=data.timestamp.dt.month, hour=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0,
                       minute=data.timestamp.dt.minute)
    
    category_orders = {opt['value']: opt.get('order') for opt in options if opt.get('order',None) is not None}

    fig = px.scatter(data, x='hour', y='value', hover_name='file', hover_data=['timestamp', 'path'], # Path last for sound sample modal
                     opacity=0.5, 
                     color=colour_by,
                     symbol=symbol_by,
                     facet_row=row_facet,
                     facet_col=col_facet,
                     category_orders=category_orders,)
    
    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(title={'text':f"Features by Time of Day ({feature})",
                             'x':0.5,
                             'y':0.95,
                             'font':{'size':24}
                             })
    
    # Adjust size of scatter dots
    fig.update_traces(marker=dict(size=dot_size))
    
    return fig