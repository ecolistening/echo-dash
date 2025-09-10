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
    Input("feature-select", "value"),
    Input("feature-range-slider", "value"),
    Input({"type": "active-filter-chip-group", "index": "acoustic-feature"}, "value"),
    State("filter-store", "data"),
    prevent_initial_call=True
)
def update_acoustic_feature_filter(
    selected_feature: str,
    selected_feature_range: List[float],
    chip_values: List[str],
    filters: Filters,
) -> Filters:
    triggered_id = ctx.triggered_id
    if ctx.triggered_id == "feature-select":
        if selected_feature == filters.get("current_feature", None):
            return no_update
        selected_feature = filters["current_feature"] if not selected_feature else selected_feature
        feature_range = tuple(filters["acoustic_features"][selected_feature])
        features = list(filters["acoustic_features"].keys())
        filters["current_feature"] = selected_feature
        filters["current_feature_range"] = feature_range
        return filters
    elif ctx.triggered_id == "feature-range-slider":
        if selected_feature_range == filters.get("current_feature_range", None):
            return no_update
        filters["current_feature_range"] = selected_feature_range
        feature_min, feature_max = selected_feature_range
        return filters
    elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("index", None) == "acoustic-feature":
        current_feature = filters["current_feature"]
        feature_min, feature_max = filters["acoustic_features"][current_feature]
        selected_values = {prefix: float(value) for prefix, value in map(lambda s: s.split("="), chip_values)}
        feature_range = [selected_values.get("start_value", feature_min), selected_values.get("end_value", feature_max)]
        if feature_range == filters.get("current_feature_range"):
            return no_update
        filters["current_feature_range"] = feature_range
        return filters
    return no_update

@callback(
    Output("feature-select", "value"),
    Output("feature-select", "data"),
    Input("filter-store", "data")
)
def update_acoustic_feature_select(
    filters: Filters
) -> Tuple[str, List[str]]:
    return filters["current_feature"], list(filters["acoustic_features"].keys())

@callback(
    Output("feature-range-slider", "min"),
    Output("feature-range-slider", "max"),
    Output("feature-range-slider", "value"),
    Output("feature-range-bounds", "children"),
    Input("filter-store", "data")
)
def update_acoustic_feature_slider(
    filters: Filters
) -> Tuple[str, List[str]]:
    feature_range = filters["current_feature_range"]
    current_feature = filters["current_feature"]
    feature_bounds = filters["acoustic_features"][current_feature]
    feature_min, feature_max = feature_bounds
    range_description = f"{feature_min} - {feature_max}"
    return feature_min, feature_max, feature_range, range_description

@callback(
    Output("acoustic-feature-range-filter-chips", "children"),
    Input("filter-store", "data"),
    prevent_initial_call=True,
)
def update_acoustic_range_filter_chips(
    filters: Filters,
) -> dmc.Accordion:
    feature = filters["current_feature"]
    feature_range = filters["current_feature_range"]
    feature_range = [
        f"{key}={feature_range[i]}"
        for i, key in enumerate(["start_value", "end_value"])
    ]
    return dmc.Accordion(
        id="active-acoustic-range-filters-accordion",
        chevronPosition="right",
        variant="separated",
        value=["acoustic-range-filter"],
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="acoustic-range-filter",
                children=[
                    dmc.AccordionControl("Acoustic Feature Range"),
                    dmc.AccordionPanel(
                        pb="1rem",
                        children=[
                            dmc.Text(
                                children=feature,
                                size="sm",
                            ),
                            dmc.Space(h="sm"),
                            dmc.ChipGroup(
                                id={"type": "active-filter-chip-group", "index": "acoustic-feature"},
                                value=feature_range,
                                multiple=True,
                                children=[
                                    dmc.Chip(
                                        variant="outline",
                                        icon=DashIconify(icon="bi-x-circle"),
                                        value=value,
                                        mt="xs",
                                        children=value,
                                    )
                                    for value in feature_range
                                ]
                            ),
                        ]
                    )
                ]
            )
        ]
    )
