import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import html, dcc, callback, clientside_callback
from dash import Output, Input, State
from dash_iconify import DashIconify

HEADER_CONFIG = {
    "height": 60,
    "color": "black",
}

def Header():
    component = dmc.AppShellHeader(
        children=[
            dmc.Group(
                p="1rem 0.5rem 1rem 0.5rem",
                grow=True,
                children=[
                    dmc.Group(
                        justify="flex-start",
                        children=[
                            dmc.Burger(
                                id="burger",
                                size="sm",
                                opened=True,
                            ),
                            dmc.Anchor(
                                children=dmc.Text(
                                    "echo-dash",
                                    c="#1D4A7A",
                                    size="xl"
                                ),
                                href="/",
                                underline="never",
                            ),
                        ]
                    ),
                    dmc.Group(
                        justify="flex-end",
                        children=[
                            dmc.Anchor(
                                children=dmc.ActionIcon(
                                    DashIconify(
                                        icon="cil:home",
                                        width=24,
                                    ),
                                    variant="light",
                                    color="blue",
                                    size="lg",
                                ),
                                href="/",
                            ),
                            dmc.Anchor(
                                children=dmc.ActionIcon(
                                    DashIconify(
                                        icon="fluent:settings-32-regular",
                                        width=24,
                                    ),
                                    variant="light",
                                    color="blue",
                                    size="lg",
                                ),
                                href="/settings"
                            ),
                            dmc.ActionIcon(
                                id="color-scheme-toggle",
                                variant="transparent",
                                color="yellow",
                                size="lg",
                                children=[
                                    dmc.Paper(DashIconify(icon="radix-icons:sun", width=24), darkHidden=True),
                                    dmc.Paper(DashIconify(icon="radix-icons:moon", width=24), lightHidden=True),
                                ],
                            ),
                        ]
                    ),
                ],
        ),
        ]
    )

    clientside_callback(
        """
        function (n, current_theme) {
            return current_theme == 'dark' ? 'plotly' : 'plotly_dark'
        }
        """,
        Output("plotly-theme", "data"),
        Input("color-scheme-toggle", "n_clicks"),
        State("color-scheme", "data"),
        prevent_initial_call=True,
    )

    clientside_callback(
        """
        function (n, current_theme) {
            next_theme = current_theme == 'dark' ? 'light' : 'dark'
            document.documentElement.setAttribute('data-mantine-color-scheme', next_theme);
            return next_theme
        }
        """,
        Output("color-scheme", "data"),
        Input("color-scheme-toggle", "n_clicks"),
        State("color-scheme", "data"),
        prevent_initial_call=True,
    )

    clientside_callback(
        """
        function (current_theme) {
            document.documentElement.setAttribute('data-mantine-color-scheme', current_theme);
            return window.dash_clientside.no_update
        }
        """,
        Output("color-scheme", "id"),
        Input("color-scheme", "data"),
    )

    return component
