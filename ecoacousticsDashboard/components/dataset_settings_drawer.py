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
            dmc.Title(
                "Settings",
                id="dataset-settings-dataset-name",
                order=2,
            ),
            dmc.Stack([
                dmc.Title('Stats', order=3),
                dmc.Text('Recordings: ', ),
                dmc.Title('Site Hierarchy', order=3),
                dmc.Stack(
                    id="dataset-settings-sites-form",
                    children=[],
                ),
            ]),
            # FIXME
            html.Div(
                children=[
                    dmc.ButtonGroup([
                        dmc.Button(
                            "Save",
                            id="dataset-settings-save-button",
                            variant="filled",
                            leftSection=DashIconify(icon="fluent:save-28-filled"),
                            n_clicks=0,
                            mb=10,
                        ),
                        dmc.Button(
                            "Cancel",
                            id="dataset-settings-cancel-button",
                            variant="filled",
                            leftSection=DashIconify(icon="material-symbols:cancel"),
                            n_clicks=0,
                            mb=10,
                        ),
                    ])
                ],
            ),
        ]
    )
