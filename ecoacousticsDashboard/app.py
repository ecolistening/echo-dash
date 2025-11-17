# Setup Logging
import os
import sys
from loguru import logger

is_production = os.environ.get("PRODUCTION") or False
logger.add(f"../log/" + "{time}.log", rotation="00:00", retention="90 days")
logger.debug(f"Python Version: {sys.version}")

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import Dash, dcc, ctx
from dash import Output, Input, State, callback, no_update
from dash_iconify import DashIconify
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

    from components.header import Header, HEADER_CONFIG
    from components.nav_bar import NavBar, NAVBAR_CONFIG
    from components.hover_icons import HoverIcons
    from components.filter_panel import FilterPanel
    from components.date_range_filter import DateRangeFilter
    from components.site_level_filter import SiteLevelFilter
    from components.environmental_filter import EnvironmentalFilter
    from components.dataset_settings_drawer import DatasetSettingsDrawer
    from store import global_store

    def SplashPage():
        return dmc.Center(
            id="landing-wrapper",
            style={
                "height": "100vh",
                "display": "flex",
                "opacity": 1,
                "transition": "opacity 1s ease",
                "position": "absolute",
                "top": 0, "left": 0, "right": 0, "bottom": 0,
                "zIndex": 9999,

            },
            children=dmc.Stack(
                align="center",
                children=[
                    dmc.Image(src="/assets/logo.png", w=350),
                    dmc.Text("Please wait while we load your data...", ta="center"),
                    dmc.Progress(id="progress-bar", value=0, striped=True, animated=True, w="50%"),
                    dcc.Interval(id="progress-interval", interval=500, n_intervals=0),
                ],
            ),
        )

    def MainPage():
        return dmc.Box(
            id="page-wrapper",
            style={"display": "block", "opacity": 0, "transition": "opacity 1s ease"},
            children=[
                Header(),
                NavBar(),
                DatasetSettingsDrawer(),
                dmc.AppShellMain([
                    FilterPanel([
                        dmc.Accordion(
                            multiple=True,
                            persistence=True,
                            children=[
                                dmc.AccordionItem(
                                    value="site",
                                    children=[
                                        dmc.AccordionControl("By Site"),
                                        dmc.AccordionPanel(SiteLevelFilter())
                                    ]
                                ),
                                dmc.AccordionItem(
                                    value="date",
                                    children=[
                                        dmc.AccordionControl("By Date"),
                                        dmc.AccordionPanel(DateRangeFilter())
                                    ]
                                ),
                                dmc.AccordionItem(
                                    value="weather",
                                    children=[
                                        dmc.AccordionControl("By Weather"),
                                        dmc.AccordionPanel(EnvironmentalFilter())
                                    ]
                                ),
                            ]
                        ),
                        dmc.Space(h="sm"),
                        dmc.Group(
                            justify="flex-end",
                            children=[
                                dmc.Button(
                                    id="filter-reset-button",
                                    children="Reset All",
                                    color="blue",
                                    w=100,
                                ),
                            ]
                        ),
                    ]),
                    dmc.Space(h="sm"),
                    dash.page_container,
                ]),
                dcc.Interval(
                    id="load-datasets",
                    interval=100,
                    max_intervals=1,
                ),
            ]
        )

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
                dcc.Store(id="init-complete", storage_type="session"),
                SplashPage(),
                MainPage(),
            ],
        )
    )

    from callbacks import nav_bar_callbacks
    nav_bar_callbacks.register_callbacks()

    from callbacks import dataset_config_callbacks
    dataset_config_callbacks.register_callbacks()

    from callbacks import filter_callbacks
    filter_callbacks.register_callbacks()

    from callbacks import page_callbacks
    page_callbacks.register_callbacks()

    for page in dash.page_registry.values():
        mod = __import__(page["module"], fromlist=["register_callbacks"])
        if hasattr(mod, "register_callbacks"):
            mod.register_callbacks()

    @callback(
        Output("progress-bar", "value"),
        Output("init-complete", "data"),
        Input("progress-interval", "n_intervals"),
        State("init-complete", "data"),
    )
    def update_progress(n, init_complete):
        if init_complete:
            return 100, no_update
        progress = min(100, n * 10)
        if progress >= 100:
            return 100, True
        return progress, no_update

    @callback(
        Output("progress-interval", "disabled"),
        Input("init-complete", "data")
    )
    def stop_interval(init_complete):
        return bool(init_complete)

    @callback(
        Output("landing-wrapper", "style"),
        Output("page-wrapper", "style"),
        Input("init-complete", "data"),
    )
    def toggle_views(init_complete):
        if init_complete:
            splash_style = {
                "display": "flex",
                "opacity": 0,
                "transition": "opacity 1s ease",
                "position": "absolute",
                "top": 0, "left": 0, "right": 0, "bottom": 0,
                "zIndex": 9999,
                "pointerEvents": "none",
            }
            app_style = {"display": "block", "opacity": 1, "transition": "opacity 1s ease"}
            return splash_style, app_style

        splash_style = {
            "display": "flex",
            "opacity": 1,
            "transition": "opacity 1s ease",
            "position": "absolute",
            "top": 0, "left": 0, "right": 0, "bottom": 0,
            "zIndex": 9999,
        }
        app_style = {"display": "block", "opacity": 0, "transition": "opacity 1s ease"}
        return splash_style, app_style

    return app

logger.info("Setup server..")
app = create_dash_app()
server = app.server

if __name__ == '__main__':
    logger.info("Start server..")
    app.run(host='0.0.0.0', debug=not is_production)
    if not is_production:
        app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    logger.info("Server shutdown.")
