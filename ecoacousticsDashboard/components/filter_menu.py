import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import pandas as pd

from dash import html, ctx, dcc, callback
from dash import Output, Input, State
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import Any, Callable, Dict, List, Tuple

def FilterMenu(
    min_date: dt.date = dt.date(1970, 1, 1),
    max_date: dt.date = dt.date.today(),
) -> dbc.Offcanvas:
    return dmc.Group(
        id="filter-menu",
        grow=True,
        style={"display": "none"},
        children=[
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        span=4,
                        children=[
                            dmc.Accordion(
                                chevronPosition="right",
                                variant="separated",
                                radius="sm",
                                children=[
                                    dmc.AccordionItem(
                                        value="dates-filter",
                                        children=[
                                            # dmc.AccordionControl("Date Range"),
                                            # dmc.AccordionPanel([
                                            #     dmc.DatePicker(
                                            #         id="date-picker",
                                            #         minDate=min_date,
                                            #         maxDate=max_date,
                                            #         value=[min_date, max_date],
                                            #     ),
                                            # ])
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                ]
            )
        ]
    )
