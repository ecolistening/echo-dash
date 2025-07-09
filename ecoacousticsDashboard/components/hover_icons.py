import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import dcc, ctx, html
from dash import Output, Input, callback
from dash_iconify import DashIconify

def HoverIcons():
    return dmc.Group(
        justify="flex-end",
        children=[
            html.Div([
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
            dmc.Divider(
                variant="solid",
                orientation="vertical"
            ),
            dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
                        children=dmc.ActionIcon(
                            DashIconify(
                                icon="uil:file-download-alt",
                                width=24,
                            ),
                            id="export-data-icon",
                            variant="light",
                            color="blue",
                            size="lg",
                            n_clicks=0,
                        ),
                    ),
                    dmc.HoverCardDropdown(
                        children=[
                            dmc.Text("Export filtered data as..."),
                            dmc.Group(
                                grow=True,
                                children=[
                                    dmc.Button("csv", variant="filled", id='dl_csv'),
                                    dmc.Button("excel", variant="filled", id='dl_xls'),
                                    dmc.Button("json", variant="filled", id='dl_json'),
                                    dmc.Button("parquet", variant="filled", id='dl_parquet'),
                                ],
                            )
                        ]
                    )
                ],
            ),
            dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
                        children=dmc.ActionIcon(
                            DashIconify(
                                icon="uil:info-circle",
                                width=24,
                            ),
                            id="info-icon",
                            variant="light",
                            color="blue",
                            size="lg",
                            n_clicks=0,
                        ),
                    ),
                    dmc.HoverCardDropdown(
                        dmc.Text("View page information"),
                    )
                ],
            ),
            dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
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
                    ),
                    dmc.HoverCardDropdown(
                        dmc.Text("View Dataset Settings"),
                    )
                ],
            ),
        ]
    )
