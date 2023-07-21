# Import packages

import dash
import dash_mantine_components as dmc
import plotly.express as px
from dash import html, dcc, callback, Output, Input, ALL

from utils import load_and_filter_dataset

dash.register_page(__name__, title='Acoustic Indices', name='Acoustic Indices')

# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
# df = pd.read_parquet(filepath).drop_duplicates()
#
# df = df.assign(hour=df.timestamp.dt.hour + df.timestamp.dt.minute / 60.0, minute=df.timestamp.dt.minute)#.astype('datetime64[ns]')
# df.time = pd.Timestamp.combine(date(2000,1,1), df.time)
# print(df.dtypes)

# fig = px.scatter(df, x='date', y='hour', symbol='recorder', hover_name='file', opacity=0.5)
# fig.update_xaxes(type='category')
# fig.update_layout(scattermode="group", scattergap=0.75)

colours_tickbox = dmc.Chip('Colour by Month', value='colour', checked=True, persistence=True, id='colour-date')

# App layout
# app.\
layout = html.Div([
    html.Div(
        [html.H1('Features by Time of Day')],
    ),
    html.Hr(),
    dmc.Group(children=[
        colours_tickbox,
    ]),
    html.Div(
        dcc.Graph(id='tod-features-graph'),
    ),
    drilldown_file_div := html.Div(),
])


# Add controls to build the interaction
@callback(
    Output('tod-features-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input('date-picker', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    # Input('checklist-locations-hierarchy', component_property='value'),
    # Input('checklist-locations', component_property='value'),
    Input('feature-dropdown', component_property='value'),
    Input(colours_tickbox, component_property='checked'),
)
def update_graph(dataset, dates, locations, feature, colour_date):
    data = load_and_filter_dataset(dataset, dates, feature, locations)
    data = data.assign(month=data.timestamp.dt.month, hour=data.timestamp.dt.hour + data.timestamp.dt.minute / 60.0,
                       minute=data.timestamp.dt.minute)
    fig = px.scatter(data, x='hour', y='value', hover_name='file', hover_data=['file', 'timestamp', 'timestamp'],
                     opacity=0.5, facet_col='recorder',
                     color='month' if colour_date else None)
    return fig

# @callback(
#     Output(drilldown_file_div, 'children'),
#     Input('tod-features-graph', 'clickData'),
#     Input('feature-dropdown', 'value'))
# def display_click_data(clickData, value):
#     if clickData is None:
#         return None
#     filename, ts, file_ts = clickData['points'][0]['customdata']
#
#     fig = px.line(data_frame=df[(df.timestamp == file_ts) & (df.feature == value)].sort_values(by='timestamp'), x='timestamp', y='value', color='recorder')
#     fig.update_xaxes(type='date')#, tickformat='%H:%M')
#
#     # Plot the feature curves
#     feature_plot = dcc.Graph(figure=fig)
#     return feature_plot
