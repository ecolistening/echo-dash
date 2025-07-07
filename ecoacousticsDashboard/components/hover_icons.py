import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import Dash, dcc, ctx
from dash import Output, Input, callback
from dash_iconify import DashIconify

def HoverIcons():
    return dmc.Group(
        justify="flex-end",
        children=[
            dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
                        children=dmc.ActionIcon(
                            DashIconify(
                                icon="uil:filter",
                                width=24,
                            ),
                            id="toggle-filter-menu",
                            variant="light",
                            color="blue",
                            size="lg",
                            n_clicks=0,
                        ),
                    ),
                    dmc.HoverCardDropdown(
                        children=[
                            dmc.Text("View filters"),
                        ]
                    )
                ]
            ),
            dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
                        children=dmc.ActionIcon(
                            DashIconify(
                                icon="uil:image-download",
                                width=24,
                            ),
                            id="image-download-icon",
                            variant="light",
                            color="blue",
                            size="lg",
                            n_clicks=0,
                        ),
                    ),
                    dmc.HoverCardDropdown(
                        children=[
                            dmc.Text("Download image as..."),
                            # FigureDownloader(page_name),
                        ]
                    )
                ],
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
        ]
    )
