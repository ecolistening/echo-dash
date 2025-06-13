import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import requests

from dash import html, dcc
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, List, Dict

import components
from store import DATASET_STORE

load_datasets_id = "load-datasets"
settings_drawer_id = "settings-drawer"
dataset_settings_button_id = "dataset-settings-button"
dataset_settings_save_button_id = "dataset-settings-save-button"
dataset_settings_cancel_button_id = "dataset-settings-cancel-button"
dataset_settings_sites_form_id = "dataset-settings-sites-form"
dataset_settings_dataset_name_id = "dataset-settings-dataset-name"

def NavBar():
    return html.Div([
        dcc.Interval(id=load_datasets_id, interval=200, max_intervals=1),
        dmc.Navbar(
            p="md",
            width=dict(base=300),
            children=dmc.ScrollArea(
                dmc.Stack(
                    children=[
                        dmc.Title("EchoDash", order=3),
                        components.Menu(),
                        dmc.Divider(),
                        dmc.Title("Data", order=3),
                        components.DatasetSelect(),
                        dmc.Button(
                            "Settings",
                            id=dataset_settings_button_id,
                            variant="filled",
                            leftIcon=DashIconify(icon="fluent:settings-32-regular"),
                            compact=True,
                            n_clicks=0,
                            mb=10,
                        ),
                        dmc.Title("Filters", order=3),
                        # filters,
                        dmc.Drawer(
                            title="Settings",
                            id=settings_drawer_id,
                            padding="md",
                            size="55%",
                            position='right',
                            zIndex=10000,
                            children=[
                                dmc.Title(
                                    "Settings",
                                    id=dataset_settings_dataset_name_id,
                                    order=2,
                                ),
                                dmc.Stack([
                                    dmc.Title('Stats', order=3),
                                    dmc.Text('Recordings: ', ),
                                    dmc.Title('Site Hierarchy', order=3),
                                    dmc.Stack(
                                        id=dataset_settings_sites_form_id,
                                        children=[],
                                    ),
                                ]),
                                dmc.Footer([
                                    dmc.ButtonGroup([
                                        dmc.Button(
                                            "Save",
                                            id=dataset_settings_save_button_id,
                                            variant="filled",
                                            leftIcon=DashIconify(icon="fluent:save-28-filled"),
                                            n_clicks=0,
                                            mb=10,
                                        ),
                                        dmc.Button(
                                            "Cancel",
                                            id=dataset_settings_cancel_button_id,
                                            variant="filled",
                                            leftIcon=DashIconify(icon="material-symbols:cancel"),
                                            n_clicks=0,
                                            mb=10,
                                        ),
                                    ])
                                ], height=60),
                            ]
                        )
                    ]
                )
            )
        )
    ])

