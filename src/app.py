# Setup Logging
import os
import sys
from loguru import logger

is_production = bool(os.environ.get("PRODUCTION")) or False
if is_production:
    logger.remove()
    logger.add(f"../log/" + "{time}.log", rotation="00:00", retention="90 days", level="WARNING")
logger.debug(f"Python Version: {sys.version}")

import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import Dash, dcc, ctx
from dash import Output, Input, State, callback, no_update
from dash_iconify import DashIconify
from typing import Any, Dict, List

THEME = {
    "fontFamily": "'Inter', sans-serif",
    # "primaryColor": "indigo",
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
        # suppress_callback_exceptions=is_production,
        external_stylesheets=[
            # dbc.icons.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
        ]
    )

    from components.header import Header
    from components.menu import Menu
    from components.filter_panel import FilterPanel
    from components.date_range_filter import DateRangeFilter
    from components.site_level_filter import SiteLevelFilter
    from components.environmental_filter import EnvironmentalFilter
    from store import global_store
    from api import dispatch, FETCH_DATASETS

    def SplashPage():
        return dmc.Center(
            id="splash-wrapper",
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
        dataset_panel = dmc.Accordion(
            chevronPosition="right",
            variant="separated",
            radius="sm",
            value="datasets",
            persistence=True,
            children=[
                dmc.AccordionItem(
                    value="datasets",
                    children=[
                        dmc.AccordionControl(
                            "Datasets",
                            icon=dmc.ActionIcon(
                                DashIconify(
                                    icon="solar:database-linear",
                                    width=24,
                                ),
                                variant="light",
                                color="blue",
                                size="lg",
                            ),
                        ),
                        dmc.AccordionPanel(
                            style={"padding": "0 0 1rem 0"},
                            children=dmc.Group(
                                grow=True,
                                children=[
                                    dmc.Box([
                                        dmc.Text(
                                            "Choose a dataset:",
                                            size="sm",
                                            span=True,
                                            mr="1rem",
                                        ),
                                        dmc.Select(
                                            id="dataset-select",
                                            style={"display": "inline-block"},
                                            searchable=True,
                                            clearable=False,
                                            allowDeselect=False,
                                            nothingFoundMessage="No datasets found...",
                                            persistence=True,
                                        ),
                                    ]),
                                ]
                            ),
                        )
                    ]
                )
            ],
        )
        return dmc.Box(
            id="page-wrapper",
            style={"display": "block", "opacity": 0, "transition": "opacity 1s ease"},
            children=[
                dmc.AppShellHeader(
                    id="header",
                    children=Header(),
                ),
                dmc.AppShellNavbar(
                    id="navbar",
                    p="md",
                    w=300,
                    children=Menu(),
                ),
                dmc.AppShellMain(
                    children=[
                        dataset_panel,
                        dmc.Space(h="sm"),
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
                    ],
                ),
                dcc.Interval(
                    id="load-datasets",
                    interval=100,
                ),
            ]
        )

    app.layout = dmc.MantineProvider(
        theme=THEME,
        withGlobalClasses=True,
        children=dmc.AppShell(
            id="appshell",
            navbar={
                "width": 300,
                "breakpoint": "sm",
                "collapsed": {
                    "desktop": False,
                    "mobile": True,
                },
            },
            header={
                "height": 60,
                "color": "black",
            },
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

    from callbacks import filter_callbacks
    filter_callbacks.register_callbacks()

    from callbacks import page_callbacks
    page_callbacks.register_callbacks()

    for page in dash.page_registry.values():
        mod = __import__(page["module"], fromlist=["register_callbacks"])
        if hasattr(mod, "register_callbacks"):
            mod.register_callbacks()

    @callback(
        Output("dataset-select", "value"),
        Output("dataset-select", "data"),
        Output("load-datasets", "disabled"),
        State("dataset-select", "value"),
        Input("load-datasets", "n_intervals"),
    )
    def fetch_datasets(current_dataset, _) -> List[Dict[str, str]]:
        action = FETCH_DATASETS
        logger.debug(f"{ctx.triggered_id=} {action=}")
        datasets = dispatch(action, default=[])
        dataset_options = [
            dict(label=dataset, value=dataset)
            for dataset in datasets
        ]
        if current_dataset is None or not len(current_dataset):
            current_dataset = dataset_options[0]["value"]
        return current_dataset, dataset_options, True

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
        Output("splash-wrapper", "style"),
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
    app.run(host='0.0.0.0', debug=False)
    # if not is_production:
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True, dev_tools_props_check=True)
    logger.info("Server shutdown.")
