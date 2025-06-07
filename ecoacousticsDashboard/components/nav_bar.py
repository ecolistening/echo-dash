import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import requests

from dash import html, dcc
from typing import Any, List

import components
from store import DATASET_STORE

load_datasets_id = "load-datasets"

def NavBar():
    return html.Div([
        dcc.Interval(id=load_datasets_id, interval=200, max_intervals=1),
        dmc.Navbar(
            p="md",
            width=dict(base=300),
            children=dmc.ScrollArea(
                dmc.Stack(
                    children=[
                        dmc.Title("EchoDash", order=3),
                        components.Menu(),
                        dmc.Divider(),
                        dmc.Title("Data", order=3),
                        components.DatasetSelect(),
                        # # dataset_settings_button,
                        dmc.Title("Filters", order=3),
                        # # filters,
                        # # settings_drawer,
                    ]
                )
            )
        )
    ])
