import dash
from dash import html

from utils.content import get_content_text

dash.register_page(__name__, title="Ecoacoustic Dashboard", name="Home", path='/')

layout = html.Div([
    html.H1('Ecoacoustic Dashboard'),
    html.Div(get_content_text('home.txt')),
])