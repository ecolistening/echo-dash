# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, dcc, callback, Output, Input, ALL, Patch
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import RobustScaler

from umap import UMAP
import numpy as np
import pandas as pd

from utils import load_and_filter_dataset, load_and_filter_sites

dash.register_page(__name__, title='UMAP', name='UMAP')

# FIXME use of 'location' is deprecated. This should select a level from 'site'
index = ['file', 'site', 'timestamp',
             'location',
             # 'hours after dawn', 'hours after sunrise', 'hours after noon', 'hours after sunset', 'hours after dusk',
             # 'dddn'
         ]
tod_timing = ['hours after dawn', 'hours after sunrise', 'hours after noon', 'hours after sunset', 'hours after dusk', 'dddn']
# Level of site
# Time breakdowns

# colours_tickbox = dmc.Chip('Colour by Recorder', value='colour', checked=True, persistence=True, id='colour-locations')
normalised_tickbox = dmc.Chip('Normalised', value='normalised', checked=False, persistence=True, id='normalised-tickbox')
diel_tickbox = dmc.Chip('Plot per Time of Day', value='diel', checked=False, persistence=True, id='separate-tod')
separate_plots_tickbox = dmc.Chip('Plot per Location', value='location', checked=False, persistence=True, id='separate-plots')

colour_select = dmc.Select(
    id='umap-plot-options-color-by',
    label="Colour by",
    data=[{'value': i, 'label': i, 'group': 'Base'} for i in index] + [{'value': i, 'label': i, 'group': 'Time of Day'} for i in tod_timing],
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
symbol_select = dmc.Select(
    id='umap-plot-options-symbol-by',
    label="Symbolise by",
    data=index,
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
row_facet_select = dmc.Select(
    id='umap-plot-options-rowfacet-by',
    label="Facet Rows by",
    data=index,
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)
col_facet_select = dmc.Select(
    id='umap-plot-options-colfacet-by',
    label="Facet Columns by",
    data=index,
    searchable=True,
    clearable=True,
    style={"width": 200},
    persistence=True
)

opacity_slider = dmc.Slider(
    id='umap-plot-options-opacity',
    min=0, max=100, step=5, value=50,
    labelAlwaysOn=True,
    marks=[
        {'value': i, 'label': f'{i}%'} for i in range(0,100,20)
    ],
    persistence=True
)

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
    # dmc.Group(children=[
    #     # time_aggregation,
    #     # colours_tickbox,
    #     # outliers_tickbox,
    #     normalised_tickbox,
    #     diel_tickbox,
    #     separate_plots_tickbox
    # ]),
    dmc.Group(children=[
        colour_select,
        symbol_select,
        row_facet_select,
        col_facet_select
    ]),
    dmc.Group([
        dmc.Text('Opacity', size='sm'),
        opacity_slider
    ], grow=True),
    dmc.Divider(variant='dotted'),
    html.Div(
        main_plot := dcc.Graph(),
    ),
    drilldown_file_div := html.Div(),
])

@callback(
    Output(colour_select, component_property='data'),
    Output(symbol_select, component_property='data'),
    Output(row_facet_select, component_property='data'),
    Output(col_facet_select, component_property='data'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
)
def update_plot_options(dataset, dates, locations):
    data = load_and_filter_dataset(dataset, dates, locations=locations)

    sitelevel_cols = list(filter(lambda a: a.startswith('sitelevel_'), data.columns))
    temporal_cols = ['hour', 'weekday', 'date', 'month', 'year']


    options = [{'value': i, 'label': i, 'group': 'Base'} for i in index] +\
              [{'value': i, 'label': i, 'group': 'Time of Day'} for i in tod_timing] +\
              [{'value': i, 'label': i, 'group': 'Site Level'} for i in sitelevel_cols] +\
              [{'value': i, 'label': i, 'group': 'Temporal'} for i in temporal_cols]

    return options, options, options, options

# Add controls to build the interaction
@callback(
    Output(main_plot, component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input('feature-dropdown', component_property='value'),
    Input(colour_select, component_property='value'),
    Input(symbol_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(opacity_slider, component_property='value'),
    # Input(diel_tickbox, component_property='checked'),
    # Input(separate_plots_tickbox, component_property='checked'),
)
def update_graph(dataset, dates, locations, feature, colour_by, symbolise_by, row_facet, col_facet, opacity):#, normalised, diel_plots, separate_plots):

    data = load_and_filter_dataset(dataset, dates, feature=None, locations=locations)

    idx_cols = list(filter(lambda a: a not in ['feature', 'value'], data.columns ))
    idx_data = data.pivot(columns='feature', index=idx_cols, values='value')
    idx_data = idx_data.loc[np.isfinite(idx_data).all(axis=1), :]

    pipe = make_pipeline(RobustScaler(), UMAP())

    proj = pipe.fit_transform(idx_data)
    graph_data = pd.DataFrame(proj, index=idx_data.index).reset_index()

    fig = px.scatter(
        graph_data, x=0, y=1,
        opacity=opacity/100.0,
        color=colour_by,
        symbol=symbolise_by,
        facet_row=row_facet,
        facet_col=col_facet,
        hover_name='file',
        hover_data=['site', 'dddn', 'timestamp'],
        # labels={'color': 'Site'},
        height=800
    )

    return fig