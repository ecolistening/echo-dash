import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, html
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, List, Dict

from store import DATASET_STORE, DATASETS_STORE

settings_drawer_id = "settings-drawer"
dataset_settings_button_id = "dataset-settings-button"
dataset_settings_sites_form_id = "dataset-settings-sites-form"
dataset_settings_dataset_name_id = "dataset-settings-dataset-name"

def DatasetSettingsButton():
    return dmc.Button(
        "Settings",
        id=dataset_settings_button_id,
        variant="filled",
        leftIcon=DashIconify(icon="fluent:settings-32-regular"),
        compact=True,
        n_clicks=0,
        mb=10,
    )

def DatasetSettingsDrawer():
    return dmc.Drawer(
        title="Settings",
        id=settings_drawer_id,
        padding="md",
        size="55%",
        position='right',
        zIndex=10000,
        children=[
            dmc.Title(
                f'Settings for the {dataset := None} dataset',
                order=2,
            ),
            dmc.Stack([
                dmc.Title('Stats', order=3),
                dmc.Text('Recordings: ', ),
                dmc.Title('Site Hierarchy', order=3),
                dmc.Stack(
                    children=[],
                    id=dataset_settings_sites_form_id
                ),
            ]),
            dmc.Footer([
                dmc.ButtonGroup([
                    dmc.Button(
                        "Save",
                        variant="filled",
                        leftIcon=DashIconify(icon="fluent:save-28-filled"),
                        id="dataset-settings-save-button",
                        n_clicks=0,
                        mb=10,
                    ),
                    dmc.Button(
                        "Cancel",
                        variant="filled",
                        leftIcon=DashIconify(icon="material-symbols:cancel"),
                        id="dataset-settings-cancel-button",
                        n_clicks=0,
                        mb=10,
                    ),
                ])
            ], height=60),
        ]
    )
