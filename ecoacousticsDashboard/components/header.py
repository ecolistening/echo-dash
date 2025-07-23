import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import html, dcc, callback
from dash import Output, Input, State
from dash_iconify import DashIconify

from components.hover_icons import HoverIcons

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
                                # dmc.Image(src=logo, h=40),
                                dmc.Title("EchoDash", c="blue"),
                            ]
                        ),
                    ),
                    dmc.GridCol(
                        span=6,
                        children=HoverIcons()
                    )
                ]
            ),
        ]
    )
