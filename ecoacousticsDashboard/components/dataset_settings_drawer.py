import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import html, dcc, callback
from dash import Output, Input, State
from dash_iconify import DashIconify

def DatasetSettingsDrawer():
    return dmc.Drawer(
        title="Settings",
        id="settings-drawer",
        padding="md",
        size="55%",
        position='right',
        zIndex=10000,
        children=[
            dmc.Stack([
                dmc.Space(h="sm"),
                dmc.Title('Site Hierarchy', order=3),
                dmc.Stack(
                    id="dataset-settings-sites-form",
                    children=[],
                ),
            ]),
            dmc.Space(h="sm"),
            dmc.Box(
                children=[
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Button(
                                "Save",
                                id="dataset-settings-save-button",
                                variant="filled",
                                color="blue",
                                leftSection=DashIconify(icon="fluent:save-28-filled"),
                                n_clicks=0,
                                mb=10,
                            ),
                            dmc.Button(
                                "Cancel",
                                id="dataset-settings-cancel-button",
                                color="red",
                                variant="filled",
                                leftSection=DashIconify(icon="material-symbols:cancel"),
                                n_clicks=0,
                                mb=10,
                            ),
                        ]
                    )
                ],
            ),
        ]
    )
