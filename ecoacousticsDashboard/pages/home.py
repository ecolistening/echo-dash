import dash
from dash import html

dash.register_page(__name__, title="EchoDash", name="EchoDash", path='/')

layout = html.Div([
    html.H1('Ecoacustic Dashboard'),
    html.Div('Here go further descriptions..'),
])
