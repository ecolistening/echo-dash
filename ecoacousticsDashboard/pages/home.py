import dash
from dash import html

dash.register_page(__name__, title="Home", name="Home", path='/')

layout = html.Div([
    html.H1('Ecoacuostic Dashboard'),
    html.Div('Here go further descriptions..'),
])