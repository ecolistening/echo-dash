import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import html, dcc, callback
from dash import Output, Input, State
from dash_iconify import DashIconify

HEADER_CONFIG = {
    "height": 60,
    "color": "black",
}

def Header():
    return dmc.AppShellHeader(
        children=[
            dmc.Grid(
                style={"padding": "1rem 0.5rem 1rem 0.5rem"},
                children=[
                    dmc.GridCol(
                        span=6,
                        children=dmc.Group(
                            justify="flex-start",
                            children=[
                                dmc.Burger(
                                    id="burger",
                                    size="sm",
                                    opened=True,
                                ),
                                dmc.Text("echo-dash", c="#1D4A7A", size="xl")
                            ]
                        ),
                    ),
                    dmc.GridCol(
                        span=5,
                        children=dmc.Group(
                            justify="flex-end",
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
                        )
                    ),
                    dmc.GridCol(
                        span=1,
                        children=dmc.Group(
                            justify="flex-end",
                            children=[
                                dmc.Anchor(
                                    children=dmc.ActionIcon(
                                        DashIconify(
                                            icon="fluent:settings-32-regular",
                                            width=24,
                                        ),
                                        id="dataset-settings-button",
                                        variant="light",
                                        color="blue",
                                        size="lg",
                                        n_clicks=0,
                                    ),
                                    href="/settings"
                                ),
                            ]
                        ),
                    ),
                ]
            ),
        ]
    )
