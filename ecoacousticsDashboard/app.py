# Setup Logging
import os
import sys
from loguru import logger

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import Dash, dcc, ctx
from dash import Output, Input, State, callback
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
        suppress_callback_exceptions=True,
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
    from callbacks import dataset_config_callbacks
    from callbacks import filter_callbacks

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("date-picker", "value"),
        Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
        State("filter-store", "data"),
        prevent_initial_call=True
    )
    def update_dates_filter(
        selected_dates: List[str],
        chip_values: List[str],
        filters,
    ):
        if ctx.triggered_id is None:
            return no_update
        if ctx.triggered_id == "date-picker":
            if selected_dates is not None and len(list(filter(None, selected_dates))) < 2:
                return no_update
            if selected_dates == filters.get("date_range", None):
                return no_update
            filters["date_range"] = selected_dates
            return filters
        elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("index", None) == "date-range":
            min_date, max_date = filters["date_range_bounds"]
            dates_dict = {prefix: date for prefix, date in map(lambda s: s.split("="), chip_values)}
            date_range = [dates_dict.get("start_date", min_date), dates_dict.get("end_date", max_date)]
            if date_range == filters.get("date_range", None):
                return no_update
            return filters
        return no_update

    return app

if __name__ == '__main__':
    logger.info("Start server..")
    app = create_dash_app()
    app.run(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    logger.info("Server shutdown.")
