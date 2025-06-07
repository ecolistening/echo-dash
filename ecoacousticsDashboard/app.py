import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import flask
import os

from dash import dcc, Output, Input, callback
from loguru import logger

from components import NavBar
from store import global_store

THEME = {
    "fontFamily": "'Inter', sans-serif",
    "primaryColor": "indigo",
    "components": {
        "Button": {"styles": {"root": {"fontWeight": 400}}},
        "Alert": {"styles": {"title": {"fontWeight": 500}}},
        "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
    },
}

def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get("secret_key", "secret")

    app = dash.Dash(
        __name__,
        server=server,
        requests_pathname_prefix=requests_pathname_prefix,
        use_pages=True,
        external_stylesheets=[
            dbc.themes.LITERA,
            dbc.icons.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
        ]
    )

    from callbacks import dataset_callbacks

    app.layout = dmc.MantineProvider(
        theme=THEME,
        inherit=True,
        withGlobalStyles=True,
        children=dmc.AppShell(
            children=[
                *global_store,
                dash.page_container,
            ],
            navbar=NavBar(),
        ),
    )

    return app
