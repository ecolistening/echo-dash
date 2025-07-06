# Setup Logging
import os
import sys
from loguru import logger

os.makedirs('log', exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")
logger.info("Setup server..")
logger.debug(f"Python Version: {sys.version}")

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import Dash, dcc
from dash import Output, Input, callback

import components
# from menu.filter import filters
from store import stores as global_store

THEME = {
    "fontFamily": "'Inter', sans-serif",
    "primaryColor": "indigo",
    "components": {
        "Button": {"styles": {"root": {"fontWeight": 400}}},
        "Alert": {"styles": {"title": {"fontWeight": 500}}},
        "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
    },
}

def create_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        # suppress_callback_exceptions=True,
        external_stylesheets=[
            dbc.themes.LITERA,
            dbc.icons.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
        ]
    )

    from callbacks import dataset_callbacks
    from callbacks import page_callbacks

    app.layout = dmc.MantineProvider(
        theme=THEME,
        inherit=True,
        withGlobalStyles=True,
        children=dmc.AppShell(
            children=[
                *global_store,
                dash.page_container,
                components.FilterMenu(),
            ],
            navbar=components.NavBar(),
        ),
    )

    return app

if __name__ == '__main__':
    logger.info("Start server..")
    app = create_dash_app()
    app.run_server(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    logger.info("Server shutdown.")
