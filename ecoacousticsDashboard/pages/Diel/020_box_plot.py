# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, ctx, dcc, callback, Output, Input, State, ALL
from loguru import logger

from utils.content import get_tabs
from utils.data import dataset_loader, filter_data
from utils.modal_sound_sample import get_modal_sound_sample
from utils.plot_filter_menu import get_filter_drop_down, get_time_aggregation
from utils.save_plot_fig import get_save_plot

PAGENAME = 'box-plot'
PAGETITLE = 'Box Plot of Descriptor by Time of Day'
PLOTHEIGHT = 800
dash.register_page(__name__, title=PAGETITLE, name='Box Plot')

colour_select, row_facet_select, col_facet_select = \
    get_filter_drop_down(PAGENAME, colour_by_cat=True, include_symbol= False,
    colour_default='recorder', col_facet_default='recorder')

time_aggregation = get_time_aggregation(PAGENAME)
outliers_tickbox = dmc.Chip('Outliers', value='outlier', checked=True, persistence=True, id='outliers-tickbox')

filter_group = dmc.Group(children=[colour_select,row_facet_select,col_facet_select,time_aggregation,outliers_tickbox])

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
    filter_group,
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    get_modal_sound_sample(PAGENAME),
    drilldown_file_div := html.Div(),
])


# Add controls to build the interaction
@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),

    # Covered by menu filter
    State('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input('feature-dropdown', component_property='value'),

    Input(colour_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(time_aggregation, component_property='value'),
    Input(outliers_tickbox, component_property='checked'),

    prevent_initial_call=True,
)
def update_graph(dataset_name, dates, locations, feature, colour_by, row_facet, col_facet, time_agg, outliers):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} dates:{len(dates)} locations:{len(locations)} {feature=} {colour_by=} {row_facet=} {col_facet=} {time_agg=} {outliers=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.acoustic_features, dates=dates, locations=locations, feature=feature)

    data = data.sort_values(by='recorder')
    data = data.assign(time=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0, hour=data.timestamp.dt.hour,
                       minute=data.timestamp.dt.minute)

    fig = px.box(data, x=time_agg, y='value',
                hover_name='file', hover_data=['file', 'timestamp', 'path'], # Path last for sound sample modal
                height=PLOTHEIGHT,
                color=colour_by,
                facet_row=row_facet,
                facet_col=col_facet,
                facet_col_wrap=4,
                points='outliers' if outliers else False,
                category_orders=dataset.category_orders())

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(title={'text':f"{PAGETITLE} ({feature})",
                             'x':0.5,
                             'y':0.97,
                             'font':{'size':24}
                             })

    return fig
