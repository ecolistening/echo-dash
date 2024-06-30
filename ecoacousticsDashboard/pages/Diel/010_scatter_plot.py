# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, ctx, dcc, callback, Output, Input, State, ALL, clientside_callback
from loguru import logger

from utils.data import load_and_filter_dataset, get_categorical_orders_for_dataset
from utils.modal_sound_sample import get_modal_sound_sample
from utils.plot_filter_menu import get_filter_drop_down, get_size_slider
from utils.save_plot_fig import get_save_plot

PAGENAME = 'scatter-plot'
PAGETITLE = 'Scatter Plot of Descriptor by Time of Day'
dash.register_page(__name__, title=PAGETITLE, name='Scatter Plot')

colour_select, symbol_select, row_facet_select, col_facet_select = get_filter_drop_down(PAGENAME, colour_default='month', row_facet_default="sitelevel_1")
size_slider_text, size_slider = get_size_slider(PAGENAME, size_slider_default=3)

filter_group = dmc.Group(children=[colour_select,symbol_select,row_facet_select,col_facet_select,size_slider_text,size_slider,dmc.Text()],grow=True)

#html.Div([size_slider_text,size_slider],style={"display": "grid", "grid-template-columns": "20% 80%"})

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
        [html.H1(PAGETITLE)],
    ),
    html.Hr(),
    filter_group,
    dmc.Divider(variant='dotted'),
    dcc.Graph(id=f'{PAGENAME}-graph'),
    appendix,
    get_modal_sound_sample(PAGENAME),
    drilldown_file_div := html.Div(),
])


@callback(
    Output(f'{PAGENAME}-graph', component_property='figure'),

    # Covered by menu filter
    State('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input('feature-dropdown', component_property='value'),

    Input(colour_select, component_property='value'),
    Input(symbol_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(size_slider, component_property='value'),

    prevent_initial_call=True,
)
def load_fig(dataset, dates, locations, feature, colour_by, symbol_by, row_facet, col_facet, dot_size):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset=} dates:{len(dates)} locations:{len(locations)} {feature=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=}")
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(month=data.timestamp.dt.month, hour=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0,
                       minute=data.timestamp.dt.minute)
    
    category_orders = get_categorical_orders_for_dataset(dataset)

    fig = px.scatter(data, x='hour', y='value', hover_name='file', hover_data=['timestamp', 'path'], # Path last for sound sample modal
                     height=600,
                     opacity=0.5, 
                     color=colour_by,
                     symbol=symbol_by,
                     facet_row=row_facet,
                     facet_col=col_facet,
                     category_orders=category_orders,)
    
    # Add centered title
    fig.update_layout(title={'text':f"{PAGETITLE} ({feature})",
                             'x':0.5,
                             'y':0.97,
                             'font':{'size':24}
                             })
    
    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Adjust size of scatter dots
    fig.update_traces(marker=dict(size=dot_size))
    
    return fig