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

from api import dispatch, FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from components.environmental_filter import EnvironmentalFilterSliderAccordion
from utils import ceil, floor

Filters = Dict[str, Any]

@callback(
    Output("weather-variable-filter-groups", "children"),
    Input("dataset-select", "value"),
)
def init_weather_filters(
    dataset_name: str
) -> List[dmc.Box]:
    opt_groups = dispatch(
        FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
        dataset_name=dataset_name,
        options=("Temperature", "Precipitation", "Wind"),
        default=[],
    )
    return [
        EnvironmentalFilterSliderAccordion(**opt_group)
        for opt_group in opt_groups
    ]

@callback(
    Output("filter-store", "data", allow_duplicate=True),
    Input({"type": "weather-variable-range-slider", "index": ALL}, "value"),
    State({"type": "weather-variable-range-slider", "index": ALL}, "id"),
    Input({"type": "weather-variable-chip-group", "index": ALL}, "value"),
    State({"type": "weather-variable-chip-group", "index": ALL}, "id"),
    State("filter-store", "data"),
    prevent_initial_call=True,
)
def update_weather_filter(
    slider_values: List[str],
    slider_ids: List[str],
    chip_values: List[str],
    chip_ids: List[str],
    filters: Filters,
) -> Filters:
    triggered_id = ctx.triggered_id
    if isinstance(ctx.triggered_id, dict) and triggered_id["type"] == "weather-variable-range-slider":
        variable_name = ctx.triggered_id["index"]
        variable_params = filters["weather_variables"][variable_name]
        ids, values = slider_ids, slider_values
        context = [(id["index"], current_range) for id, current_range in zip(ids, values) if id["index"] == variable_name]
        if not len(context):
            return no_update
        _, current_range = context[0]
        update = current_range != variable_params['variable_range']
        if not update:
            return no_update
        filters["weather_variables"][variable_name]["variable_range"] = current_range
        return filters
    elif isinstance(ctx.triggered_id, dict) and triggered_id["type"] == "weather-variable-chip-group":
        variable_name = ctx.triggered_id["index"]
        variable_params = filters["weather_variables"][variable_name]
        ids, values = chip_ids, chip_values
        context = [(id["index"], current_range) for id, current_range in zip(ids, values) if id["index"] == variable_name]
        if not len(context):
            return no_update
        _, current_range = context[0]
        selected_values = {prefix: float(value) for prefix, value in map(lambda s: s.split("="), current_range)}
        variable_min, variable_max = variable_params["variable_range_bounds"]
        current_range = [selected_values.get("start_value", variable_min), selected_values.get("end_value", variable_max)]
        update = current_range != variable_params['variable_range']
        if not update:
            return no_update
        filters["weather_variables"][variable_name]["variable_range"] = current_range
        return filters
    return no_update

@callback(
    Output({"type": "weather-variable-range-slider", "index": ALL}, "value"),
    Input("filter-store", "data")
)
def update_weather_variable_slider(
    filters: Filters
) -> Tuple[str, List[str]]:
    return list(map(lambda params: params["variable_range"], filters["weather_variables"].values()))

@callback(
    Output("weather-variable-filter-chips", "children"),
    Input("filter-store", "data"),
    prevent_initial_call=True,
)
def update_weather_filter_chips(
    filters: Filters,
) -> dmc.Accordion:
    return dmc.Accordion(
        id="active-weather-variable-filters-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        value=["weather-variable-filter"],
        children=[
            dmc.AccordionItem(
                value="weather-variable-filter",
                children=[
                    dmc.AccordionControl("Environmental"),
                    dmc.AccordionPanel(
                        pb="1rem",
                        children=[
                            dmc.Box([
                                dmc.Space(h="sm"),
                                dmc.Text(
                                    children=variable_name,
                                    size="sm",
                                ),
                                dmc.Space(h="sm"),
                                dmc.ChipGroup(
                                    id={"type": "weather-variable-chip-group", "index": variable_name },
                                    value=list(map(lambda s: "=".join(map(str, s)), zip(["start_value", "end_value"], variable_params["variable_range"]))),
                                    multiple=True,
                                    children=[
                                        dmc.Chip(
                                            variant="outline",
                                            icon=DashIconify(icon="bi-x-circle"),
                                            value=f"{suffix}={value}",
                                            mt="xs",
                                            children=f"{suffix}={value}",
                                        )
                                        for suffix, value in zip(["start_value", "end_value"], variable_params["variable_range"])
                                    ],
                                ),
                            ])
                            for variable_name, variable_params in filters["weather_variables"].items()
                        ]
                    )
                ]
            )
        ]
    )
