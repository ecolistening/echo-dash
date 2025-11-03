import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd

from dash import callback, ctx, dcc, no_update, clientside_callback
from dash import Input, State, Output
from dash_iconify import DashIconify
from loguru import logger
from io import StringIO

from typing import Any, Callable, Dict, List, Tuple

def DataDownloadWidget(
    context: str,
    dl_types: List[str] = ["csv", "json", "excel", "parquet"],
    **kwargs: Any,
) -> dmc.Box:
    return dmc.HoverCard(
        children=[
            dcc.Download(id=f"{context}-data-download"),
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
                            dmc.Button(
                                id={"type": f"{context}-data-download-button", "index": dl_type},
                                children=dl_type,
                                variant="filled",
                            )
                            for dl_type in dl_types
                        ],
                    )
                ]
            )
        ],
    )
