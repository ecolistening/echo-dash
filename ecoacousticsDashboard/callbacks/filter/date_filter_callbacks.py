import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import itertools

from dash import callback, ctx, no_update, dcc
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from utils import ceil, floor

Filters = Dict[str, Any]

@callback(
    Output("filter-store", "data", allow_duplicate=True),
    Input("date-picker", "value"),
    Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
    State("filter-store", "data"),
    prevent_initial_call=True
)
def update_dates_filter(
    selected_dates: List[str],
    chip_values: List[str],
    filters: Filters,
) -> Filters:
    if ctx.triggered_id is None:
        return no_update
    if ctx.triggered_id == "date-picker":
        if selected_dates is not None and len(list(filter(None, selected_dates))) < 2:
            return no_update
        if selected_dates == filters.get("date_range", None):
            return no_update
        filters["date_range"] = selected_dates
        return filters
    elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("index", None) == "date-range":
        min_date, max_date = filters["date_range_bounds"]
        dates_dict = {prefix: date for prefix, date in map(lambda s: s.split("="), chip_values)}
        date_range = [dates_dict.get("start_date", min_date), dates_dict.get("end_date", max_date)]
        if date_range == filters.get("date_range", None):
            return no_update
        filters["date_range"] = date_range
        return filters
    return no_update

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Input("filter-store", "data")
)
def update_date_picker(
    filters: Filters,
) -> Tuple[str, str, str]:
    date_range = filters["date_range"]
    min_date, max_date = filters["date_range_bounds"]
    return min_date, max_date, date_range

@callback(
    Output("date-range-filter-chips", "children"),
    Input("filter-store", "data"),
    prevent_initial_call=True,
)
def update_date_filter_chips(
    filters: Filters,
) -> dmc.Accordion:
    selected_dates = filters["date_range"]
    if not len(selected_dates):
        return []
    date_range = [
        f"{key}={selected_dates[i]}"
        for i, key in enumerate(["start_date", "end_date"])
    ]
    return dmc.Accordion(
        id="date-range-filters-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        value=["dates-filter"],
        children=[
            dmc.AccordionItem(
                value="dates-filter",
                children=[
                    dmc.AccordionControl("Date Range"),
                    dmc.AccordionPanel(
                        pb="1rem",
                        children=dmc.ChipGroup(
                            id={"type": "active-filter-chip-group", "index": "date-range"},
                            value=date_range,
                            multiple=True,
                            children=[
                                dmc.Chip(
                                    variant="outline",
                                    icon=DashIconify(icon="bi-x-circle"),
                                    value=value,
                                    mt="xs",
                                    children=value,
                                )
                                for value in date_range
                            ]
                        )
                    )
                ]
            )
        ]
    )
