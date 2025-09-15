# Setup Logging
import os
import sys
from loguru import logger

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import Dash, dcc, ctx
from dash import Output, Input, State, callback, no_update
from dash_iconify import DashIconify
from typing import Any, Dict, List

os.makedirs('log', exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")
logger.info("Setup server..")
logger.debug(f"Python Version: {sys.version}")

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

    from components.header import Header, HEADER_CONFIG
    from components.nav_bar import NavBar, NAVBAR_CONFIG
    from components.hover_icons import HoverIcons
    from components.dataset_settings_drawer import DatasetSettingsDrawer
    from store import global_store

    app.layout = dmc.MantineProvider(
        theme=THEME,
        withGlobalClasses=True,
        children=dmc.AppShell(
            id="appshell",
            navbar=NAVBAR_CONFIG,
            header=HEADER_CONFIG,
            padding="md",
            children=[
                *global_store,
                Header(),
                NavBar(),
                DatasetSettingsDrawer(),
                dmc.AppShellMain([
                    dash.page_container,
                ]),
                dcc.Interval(
                    id="load-datasets",
                    interval=100,
                    max_intervals=1,
                ),
            ],
        )
    )

    from callbacks import nav_bar_callbacks
    nav_bar_callbacks.register_callbacks()

    from callbacks import dataset_config_callbacks
    dataset_config_callbacks.register_callbacks()

    from callbacks import filter_callbacks
    filter_callbacks.register_callbacks()

    for page in dash.page_registry.values():
        mod = __import__(page["module"], fromlist=["register_callbacks"])
        if hasattr(mod, "register_callbacks"):
            mod.register_callbacks()

    return app

is_production = os.environ.get("PRODUCTION") or False
app = create_dash_app()
server = app.server

if __name__ == '__main__':
    logger.info("Start server..")
    app.run(host='0.0.0.0', debug=not is_production)
    if not is_production:
        app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    logger.info("Server shutdown.")
