# Import packages
from io import StringIO

import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import plotly.express as px

from dash import html, dcc, clientside_callback, callback, Output, Input, ALL, ctx, State
from functools import lru_cache
from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from umap import UMAP

from utils import list2tuple
from utils.data import load_and_filter_dataset, load_config
from utils.modal_sound_sample import get_modal_sound_sample, get_modal_state
from utils.save_plot_fig import get_save_plot

PAGENAME = 'UMAP'
dash.register_page(__name__, title=PAGENAME, name=PAGENAME)

# tod_timing = [{'value': 'dddn', 'label': 'Dawn/Day/Dusk/Night', 'type': 'categorical'}] + \
#             [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]


# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#         Layout        #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

# colours_tickbox = dmc.Chip('Colour by Recorder', value='colour', checked=True, persistence=True, id='colour-locations')
normalised_tickbox = dmc.Chip('Normalised', value='normalised', checked=False, persistence=True,
                              id='normalised-tickbox')
diel_tickbox = dmc.Chip('Plot per Time of Day', value='diel', checked=False, persistence=True, id='separate-tod')
separate_plots_tickbox = dmc.Chip('Plot per Location', value='location', checked=False, persistence=True,
                                  id='separate-plots')

colour_select = dmc.Select(
    id='umap-plot-options-color-by',
    label="Colour by",
    # data=[{'value': i, 'label': i, 'group': 'Base'} for i in index] + [{'value': i, 'label': i, 'group': 'Time of Day'} for i in tod_timing],
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
symbol_select = dmc.Select(
    id='umap-plot-options-symbol-by',
    label="Symbolise by",
    # data=index,
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
row_facet_select = dmc.Select(
    id='umap-plot-options-rowfacet-by',
    label="Facet Rows by",
    # data=index,
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
col_facet_select = dmc.Select(
    id='umap-plot-options-colfacet-by',
    label="Facet Columns by",
    # data=index,
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)

opacity_slider = dmc.Slider(
    id='umap-plot-options-opacity',
    min=0, max=100, step=5, value=50,
    marks=[
        {'value': i, 'label': f'{i}%'} for i in range(0, 100, 20)
    ],
    persistence=True
)

sample_slider = dmc.Slider(
    id='umap-plot-options-sample',
    persistence=True
)

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

        dmc.Col(html.Div(children=[
            dmc.Title('About', order=2),
            dmc.Text('A UMAP is a way of projecting high-dimensional data onto fewer dimensions.'),
            dmc.Anchor('[details]', href='https://pair-code.github.io/understanding-umap/', target="_blank"), # target="_blank" opens link in a new tab
        ]), span=4),

        dmc.Col(html.Div(children=[
            dmc.Title('Download Data', order=2),
            dmc.Text('Download the data in the current plot. Select a format below.'),
            dmc.ButtonGroup([
                dmc.Button("csv", variant="filled", id='dl_csv'),
                dmc.Button("excel", variant="filled", id='dl_xls'),
                dmc.Button("json", variant="filled", id='dl_json'),
                dmc.Button("parquet", variant="filled", id='dl_parquet'),
            ]),
            dcc.Download(id='download-dataframe'),
            dcc.Store(id='plot-data'),
            dcc.Store(id='plot-data-umap')
        ]), span=4),

        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),

    ],
    gutter="xl",
)

layout = html.Div([
    dmc.Title(PAGENAME, order=1),
    dmc.Divider(variant='dotted'),
    dmc.Group(children=[
        colour_select,
        symbol_select,
        row_facet_select,
        col_facet_select
    ]),
    dmc.Group([
        dmc.Text('Opacity', size='sm', align='right'),
        opacity_slider,
        dmc.Text('Sample Size', size='sm', align='right'),
        sample_slider
    ], grow=True),
    dmc.Divider(variant='dotted'),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    get_modal_sound_sample(PAGENAME),
    drilldown_file_div := html.Div(),
    appendix
])


# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#         Cache         #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

@lru_cache(maxsize=10)
def get_idx_data_lru(dataset:str, dates:tuple, locations:tuple):
    data = load_and_filter_dataset(dataset, dates=dates, locations=locations)

    sample_no = data.shape[0]
    logger.debug(f"Dataset {dataset} shape: {data.shape}.")

    logger.debug(f"Load config..")
    config = load_config(dataset)

    # Updating Plot
    idx_cols = list(filter(lambda a: a not in ['feature', 'value'], data.columns))

    # FIXME This is a bit of a hack. The dataset should be clean by the time it gets here.
    logger.debug(f"Check for duplicates..")
    data_nodup = data.drop_duplicates(subset=idx_cols + ['feature'], keep='first')
    if sample_no>data_nodup.shape[0]:
        logger.debug(f"Removed {sample_no-data_nodup.shape[0]} duplicate samples.")

    logger.debug(f"Select columns {idx_cols}")
    idx_data = data_nodup.pivot(columns='feature', index=idx_cols, values='value')

    sample_no = idx_data.shape[0]
    idx_data = idx_data.loc[np.isfinite(idx_data).all(axis=1), :]
    if sample_no>idx_data.shape[0]:
        logger.debug(f"Removed {sample_no-idx_data.shape[0]} NaN samples.")


    # Updating Plot Options
    options = []

    # Add site hierarchies
    sitelevel_cols = list(filter(lambda a: a.startswith('sitelevel_'), data.columns))
    options += [{'value': feat, 'label': config.get( 'Site Hierarchy', feat, fallback=feat), 'group': 'Site Level', 'type': 'categorical'} for feat in sitelevel_cols]

    # Add time of the day
    options += [{'value': 'dddn', 'label': 'Dawn/Day/Dusk/Night', 'group': 'Time of Day', 'type': 'categorical'}]
    options += [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'group': 'Time of Day', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]

    # Add temporal columns with facet order
    temporal_cols = (   
                        ('hour', list(range(24))),
                        ('weekday', ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
                        ('date', sorted(data['date'].unique())),
                        ('month', ('January','February','March','April','May','June','July','August','September','October','November','December')),
                        ('year', sorted(data['year'].unique())),
                    )
    options += [{'value': feat, 'label': feat.capitalize(), 'group': 'Temporal', 'type': 'categorical', 'order': order} for feat,order in temporal_cols]

    # deprecated since they are already covered or offer no visualisation value
    # index = ['file', 'site', 'timestamp', 'location']
    # [{'value': i, 'label': i.capitalize(), 'group': 'Other Metadata'} for i in index]

    # Filter options to ensure they are present in the dataset
    options = [opt for opt in options if opt['value'] in idx_cols]

    return idx_data, options

# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#       Functions       #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

def get_idx_data(dataset, dates, locations):
    logger.debug(f"Get index data: {dataset=} {dates=} {locations=}")
    return get_idx_data_lru(str(dataset), list2tuple(dates), list2tuple(locations))

def get_graph_data(idx_data, sample):

    # Random Sample
    if sample < idx_data.shape[0]:
        logger.debug(f"Select {sample}/{idx_data.shape[0]} random samples..")
        sel_data = idx_data.sample(n=sample, axis=0)
    else:
        sel_data = idx_data

    pipe = make_pipeline(RobustScaler(), UMAP())

    logger.debug(f"Apply RobustScaler and UMAP..")
    proj = pipe.fit_transform(sel_data)

    logger.debug(f"Write results into pd dataframe..")
    graph_data = pd.DataFrame(proj, index=sel_data.index).reset_index()

    logger.debug(f"Return graph data and selected samples.")
    return graph_data, sel_data

def get_UMAP_fig(graph_data, options, colour_by, symbol_by, row_facet, col_facet, opacity):

    logger.debug(f"Generate UMAP plot for graph data {graph_data.shape} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {opacity=}")    

    category_orders = {opt['value']: opt.get('order') for opt in options if opt.get('order',None) is not None}

    fig = px.scatter(
        graph_data, x=0, y=1,
        opacity=opacity / 100.0,
        color=colour_by,
        symbol=symbol_by,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=category_orders,
        hover_name='file',
        hover_data=['site', 'dddn', 'timestamp'],
        # labels={'color': 'Site'},
        height=800
    )

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(title={'text':f"UMAP",
                             'x':0.5,
                             'y':0.92,
                             'font':{'size':24}
                             })

    return fig


# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#       Callbacks       #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

@callback(
    Output("download-dataframe", "data"),
    State('dataset-select', component_property='value'),
    State("plot-data", "data"),
    Input("dl_csv", "n_clicks"),
    Input("dl_xls", "n_clicks"),
    Input("dl_json", "n_clicks"),
    Input("dl_parquet", "n_clicks"),
    prevent_initial_call=True,
)
def download_data(dataset, json_data, *args, **kwargs):
    logger.debug(f"Trigger Callback: {dataset=} json data ({len(json_data)}B) {ctx.triggered_id=}")

    data = pd.read_json(StringIO(json_data), orient='table')

    if ctx.triggered_id == 'dl_csv':
        return dcc.send_data_frame(data.to_csv, f'{dataset}.csv')
    elif ctx.triggered_id == 'dl_xls':
        return dcc.send_data_frame(data.to_excel, f'{dataset}.xlsx', sheet_name="Sheet_name_1")
    elif ctx.triggered_id == 'dl_json':
        return dcc.send_data_frame(data.to_json, f'{dataset}.json')
    elif ctx.triggered_id == 'dl_parquet':
        return dcc.send_data_frame(data.to_parquet, f'{dataset}.parquet')


#########################################################################################################
#   Pre-load the dataset and update the sample slider, which will trigger the main data load function   #
#########################################################################################################
@callback(
    Output(sample_slider, 'min'),
    Output(sample_slider, 'max'),
    Output(sample_slider, 'step'),
    Output(sample_slider, 'value'),
    Output(sample_slider, 'marks'),

    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, component_property='value'),
    State(sample_slider, component_property='value'), 
)
def update_sample_slider(dataset, dates, locations, sample):
    '''
    Handle any dataset changes
    '''
    logger.debug(f"Trigger Callback: {dataset=} {dates=} {locations=} {sample=}")

    idx_data, _ = get_idx_data(dataset, dates, locations)

    # Sort out sample slider
    min_sample = 1
    max_sample = idx_data.shape[0]
    step = 1
    sample = sample if sample is not None and sample <= max_sample else (1000 if max_sample > 1000 else max_sample)
    marks = [
        {'value': i, 'label': f'{i}'} for i in np.linspace(1, max_sample, num=5, endpoint=True, dtype=int)
    ]

    return min_sample, max_sample, step, sample, marks

@callback(
    Output("plot-data", component_property="data"),
    Output('plot-data-umap', component_property='data'),

    Output(f'{PAGENAME}-graph', component_property='figure', allow_duplicate=True),
    Output(colour_select, component_property='data'),
    Output(symbol_select, component_property='data'),
    Output(row_facet_select, component_property='data'),
    Output(col_facet_select, component_property='data'),

    Output(colour_select, component_property='value'),
    Output(symbol_select, component_property='value'),
    Output(row_facet_select, component_property='value'),
    Output(col_facet_select, component_property='value'),

    State('dataset-select', component_property='value'),
    State('date-picker', component_property='value'),
    State({'type': 'checklist-locations-hierarchy', 'index': ALL}, component_property='value'), 
    Input(sample_slider, component_property='value'),

    State(colour_select, component_property='value'),
    State(symbol_select, component_property='value'),
    State(row_facet_select, component_property='value'),
    State(col_facet_select, component_property='value'),
    State(opacity_slider, component_property='value'),

    prevent_initial_call=True
)
def update_dataset(dataset, dates, locations, sample, colour_by, symbol_by, row_facet, col_facet, opacity):
    '''
    Dataset changes will change sample_slider, which will trigger this function. Has to be seperated to allow trigger by initial call.
    '''
    logger.debug(f"Trigger Callback: {dataset=} {dates=} {locations=} {sample=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {opacity=}")
    idx_data, all_options = get_idx_data(dataset, dates, locations)
    graph_data, sel_data = get_graph_data(idx_data, sample)

    # Select only categorical options
    cat_options = [opt for opt in all_options if opt['type'] in ('categorical')]

    # Ensure option is available for dataset
    val_all_options = [opt['value'] for opt in all_options]
    val_cat_options = [opt['value'] for opt in cat_options]

    if colour_by not in val_all_options: colour_by = None
    if symbol_by not in val_cat_options: symbol_by = None
    if row_facet not in val_cat_options: row_facet = None
    if col_facet not in val_cat_options: col_facet = None

    fig = get_UMAP_fig(graph_data, all_options, colour_by, symbol_by, row_facet, col_facet, opacity)

    return  sel_data.to_json(date_format='iso', orient='table'), \
            graph_data.to_json(date_format='iso', orient='split'), \
            fig, all_options, cat_options, cat_options, cat_options,  \
            colour_by, symbol_by, row_facet, col_facet



@callback(
    Output(f'{PAGENAME}-graph', component_property='figure', allow_duplicate=True),

    State('plot-data-umap', component_property='data'),
    State(colour_select, component_property='data'),

    Input(colour_select, component_property='value'),
    Input(symbol_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(opacity_slider, component_property='value'),

    prevent_initial_call=True
)
def update_graph_visuals(json_data, options, colour_by, symbol_by, row_facet, col_facet, opacity):
    logger.debug(f"Trigger Callback: json data ({len(json_data)}B) {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {opacity=}")
    graph_data = pd.read_json(StringIO(json_data), orient='split')

    # Revert automatic formatting
    graph_data['date'] = graph_data['date'].astype(str)

    fig = get_UMAP_fig(graph_data, options, colour_by, symbol_by, row_facet, col_facet, opacity)

    return fig

@callback(
    Output(f'modal_sound_sample_{PAGENAME}', 'is_open'),
    Output(f'modal_sound_header_{PAGENAME}', 'children'),
    Output(f'modal_sound_file_{PAGENAME}', 'children'),
    Output(f'modal_sound_audio_{PAGENAME}', 'src'),
    Output(f'modal_sound_audio_{PAGENAME}', 'controls'),
    Output(f'modal_sound_details_{PAGENAME}', 'children'),
    
    Input(f'{PAGENAME}-graph', component_property='selectedData'),

    State('dataset-select', component_property='value'),

    suppress_callback_exceptions=True,
    prevent_initial_call=True,
)
def display_sound_modal(selectedData, dataset):
    logger.debug(f"Trigger Callback: {selectedData=} {dataset=}")
    selected, return_values = get_modal_state(selectedData,dataset)
    if not selected:
        return return_values

    pt = selectedData['points'][0]

    return *return_values, [' | '.join(pt['customdata'])]