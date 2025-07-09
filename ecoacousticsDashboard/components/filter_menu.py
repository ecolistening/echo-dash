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

def FilterMenu() -> dbc.Offcanvas:
    style_hidden = dict(display="none")
    style_visible = dict(display="block")

    @callback(
        Output("filter-menu", "style"),
        Input("toggle-filter-menu", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_filter_menu(n_clicks: int) -> bool:
        return style_visible if n_clicks % 2 == 1 else style_hidden

    return dmc.Group(
        id="filter-menu",
        grow=True,
        style=style_hidden,
        children=[
            dmc.Title("Filters", order=3),
            dmc.Stack(
                children=[
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Accordion(
                                chevronPosition="right",
                                variant="separated",
                                radius="sm",
                                children=[
                                    dmc.AccordionItem(
                                        value="acoustic-feature-filter",
                                        children=[
                                            dmc.AccordionControl("Acoustic Feature"),
                                            dmc.AccordionPanel(
                                                children=dmc.Stack(
                                                    children=[
                                                        dmc.Select(
                                                            id="feature-dropdown",
                                                            searchable=True,
                                                            clearable=False,
                                                            persistence=True,
                                                        ),
                                                        dmc.RangeSlider(
                                                            id="acoustic-feature-range",
                                                            mb=35,
                                                        ),
                                                    ]
                                                )
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            dmc.Accordion(
                                chevronPosition="right",
                                variant="separated",
                                radius="sm",
                                children=[
                                    dmc.AccordionItem(
                                        value="dates-filter",
                                        children=[
                                            dmc.AccordionControl("Filter by Date"),
                                            dmc.AccordionPanel(
                                                children=[
                                                    dmc.DatePicker(
                                                        id="date-picker",
                                                        type="range",
                                                        minDate=dt.date(1970, 1, 1),
                                                        maxDate=dt.date.today(),
                                                        value=[dt.date(1970, 1, 1), dt.date.today()],
                                                        persistence=True,
                                                        allowDeselect=False,
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Accordion(
                                chevronPosition="right",
                                variant="separated",
                                radius="sm",
                                children=[
                                    dmc.AccordionItem(
                                        value="weather-filter",
                                        children=[
                                            dmc.AccordionControl("Filter by Weather"),
                                            dmc.AccordionPanel(
                                                children=[]
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            dmc.Accordion(
                                chevronPosition="right",
                                variant="separated",
                                radius="sm",
                                children=[
                                    dmc.AccordionItem(
                                        value="other-filter",
                                        children=[
                                            dmc.AccordionControl("Filter by Something else"),
                                            dmc.AccordionPanel(
                                                children=[
                                                    dmc.Text("Some different things:")
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),
                ]
            )
        ]
    )
