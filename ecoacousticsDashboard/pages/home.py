import dash
from dash import html

from utils.content import get_content

dash.register_page(
    __name__,
    title="Ecoacoustic Dashboard",
    name="Home",
    path='/',
)

def layout():
    return html.Div(
        get_content('page/home'),
        style={'margin-left': '3em', 'width': '1000px'},
    )
