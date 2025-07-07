import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import html, dcc
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, List, Dict

import components

def NavBar():
    return dmc.AppShellNavbar(
        id="navbar",
        p="md",
        w=dict(base=300),
        children=dmc.ScrollArea(
            dmc.Stack(
                children=[
                    components.Menu(),
                    dmc.Divider(),
                    dmc.Title("Data", order=3),
                    dmc.Select(
                        id="dataset-select",
                        label="Dataset",
                        description="Select a dataset to explore",
                        searchable=True,
                        clearable=False,
                        allowDeselect=False,
                        nothingFoundMessage="Nothing datasets found...",
                        persistence=True,
                    ),
                    dmc.Button(
                        "Settings",
                        id="dataset-settings-button",
                        variant="filled",
                        leftSection=DashIconify(icon="fluent:settings-32-regular"),
                        n_clicks=0,
                        mb=10,
                    ),
                    dmc.Title("Filters", order=3),
                    dmc.Stack(
                        children=[
                            dmc.Select(
                                label="Acoustic Descriptor",
                                description="Select an acoustic desscriptor",
                                id="feature-dropdown",
                                data=[],
                                value="",
                                searchable=True,
                                clearable=False,
                                persistence=True,
                            ),
                            dmc.DatePickerInput(
                                id="date-picker",
                                type="range",
                                label="Date Range",
                                description="To include in plots",
                                minDate=dt.date(1970, 1, 1),
                                maxDate=dt.date.today(),
                                value=[dt.date(1970, 1, 1), dt.date.today()],
                                clearable=True,
                                persistence=True,
                            ),
                        ]
                    ),
                    dmc.Drawer(
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
                ]
            )
        )
    )

