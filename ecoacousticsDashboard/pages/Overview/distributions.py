# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger

from utils.content import get_tabs
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.plot_filter_menu import get_filter_drop_down
from utils.save_plot_fig import get_save_plot

PAGENAME = 'distributions'
PAGETITLE = 'Soundscape Descriptor Distributions'
PLOTHEIGHT = 800
dash.register_page(__name__, title=PAGETITLE, name='Distributions')

colour_select, row_facet_select, col_facet_select = \
    get_filter_drop_down(PAGENAME, colour_by_cat=True, include_symbol= False,
    colour_default='location', row_facet_default='location', col_facet_default='dddn')

normalised_tickbox = dmc.Chip('Normalised', value='normalised', checked=False, persistence=True,
                              id='normalised-tickbox')

filter_group = dmc.Group(children=[colour_select,row_facet_select,col_facet_select,normalised_tickbox])

appendix = dmc.Grid(
    children=[
        dmc.Col(get_tabs(PAGENAME), span=8),
        dmc.Col(get_save_plot(f'{PAGENAME}-graph'), span=4),
    ],
    gutter="xl",
)

layout = html.Div([
    dmc.Title(PAGETITLE, order=1),
    dmc.Divider(variant='dotted'),
    filter_group,
    dcc.Graph(id=f'{PAGENAME}-graph'),
    drilldown_file_div := html.Div(),
    appendix,
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
    Input(normalised_tickbox, component_property='checked'),

    prevent_initial_call=True,
)
def update_graph(dataset_name, dates, locations, feature, colour_by, row_facet, col_facet, normalised):  # , time_agg, outliers, colour_locations, ):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} dates:{len(dates)} locations:{len(locations)} {feature=} {colour_by=} {row_facet=} {col_facet=} {normalised=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    data = filter_data(dataset.acoustic_features, dates=dates, feature=feature, locations=locations)

    fig = px.histogram(
        data, x='value', marginal='rug', opacity=0.75, height=PLOTHEIGHT,
        color=colour_by,
        facet_row=row_facet,
        facet_col=col_facet,
        histnorm='percent' if normalised else None,
        category_orders=DatasetDecorator(dataset).category_orders(),
    )

    # Add centered title
    fig.update_layout(title={'text':f"{PAGETITLE} ({feature})",
                             'x':0.5,
                             'y':0.97,
                             'font':{'size':24}
                             })

    return fig
