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

from dash import Dash, dcc, ctx
from dash import Output, Input, callback
from typing import Any, Dict, List

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
        external_stylesheets=[
            dbc.themes.LITERA,
            dbc.icons.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
        ]
    )

    import components
    from store import global_store

    app.layout = dmc.MantineProvider(
        theme=THEME,
        withGlobalClasses=True,
        children=dmc.AppShell(
            children=[
                *global_store,
                components.NavBar(),
                dmc.AppShellMain([
                    # components.FilterMenu(),
                    dash.page_container,
                ]),
                dcc.Interval(
                    id="load-datasets",
                    interval=100,
                    max_intervals=1
                ),
            ],
        ),
    )

    from callbacks import nav_bar_callbacks
    from callbacks import dataset_config_callbacks
    from callbacks import page_callbacks
    from callbacks import graph_param_callbacks

    return app

if __name__ == '__main__':
    logger.info("Start server..")
    app = create_dash_app()
    app.run(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    logger.info("Server shutdown.")
