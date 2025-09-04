import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import callback, ctx, no_update, dcc
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_DATASETS,
    FETCH_FILES,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_WEATHER,
)
from utils import ceil, floor

Filters = Dict[str, Any]

@callback(
    Output("filter-store", "data"),
    Input("dataset-select", "value"),
    State("filter-store", "data"),
)
def init_dataset_filters(
    dataset_name: str,
    filters: Filters,
) -> Filters:
    logger.debug(filters)
    filters = {} if filters is None else filters
    # set dates and date range
    data = dispatch(FETCH_FILES, dataset_name=dataset_name)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    date_range = (min_date, max_date)
    filters["date_range_bounds"] = date_range
    filters["date_range"] = date_range
    # set feature and feature range
    data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
    features = data["feature"].unique()
    current_feature = filters.get("current_feature", features[0])
    feature_data = data.loc[data["feature"] == current_feature, "value"]
    feature_min = floor(feature_data.min(), precision=2)
    feature_max = ceil(feature_data.max(), precision=2)
    acoustic_features = {}
    for feature in features:
        df = data.loc[data["feature"] == feature, "value"]
        acoustic_features[feature] = (floor(df.min(), precision=2), ceil(df.max(), precision=2))
    filters["acoustic_features"] = acoustic_features
    filters["current_feature"] = current_feature
    filters["current_feature_range"] = tuple(filters["acoustic_features"][current_feature])
    # set weather variables and default ranges
    data = dispatch(FETCH_WEATHER, dataset_name=dataset_name)
    weather_variables = {}
    for variable in data.variable.unique():
        df = data.loc[data["variable"] == variable, "value"]
        variable_ranges = {}
        variable_range = (floor(df.min()), ceil(df.max()))
        variable_ranges["variable_range_bounds"] = variable_range
        variable_ranges["variable_range"] = variable_range
        weather_variables[variable] = variable_ranges
    filters["weather_variables"] = weather_variables
    return filters

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

# FIXME:
# we're getting a double update here for some reason, coupled to acoustic feature range slider somehow?
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
    variable_name = ctx.triggered_id["index"]
    variable_params = filters["weather_variables"][variable_name]
    if triggered_id["type"] == "weather-variable-range-slider":
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
    elif triggered_id["type"] == "weather-variable-chip-group":
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

# @callback(
#     Output("filter-state", "children"),
#     Input("filter-store", "data"),
#     Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
# )
# def update_active_filters(
#     filters: Dict[str, Any],
#     discluded_file_ids: str,
#     locations: List[str],
# ) -> dmc.AccordionItem:
#     no_active_filters = (
#         (not len(filters["date_range"])) and
#         (not len(filters["current_feature_range"])) and
#         (discluded_file_ids is None or not len(discluded_file_ids)) and
#         (locations is None or not len(locations))
#     )
#     if no_active_filters:
#         return "No filters currently active"
#     return ""

# @callback(
#     Output("site-filter-chips", "children"),
#     State("dataset-config", "data"),
#     Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
#     prevent_initial_call=True,
# )
# def update_active_site_filters(
#     config: Dict[str, str],
#     locations: List[str],
# ) -> dmc.Accordion:
#     if not len(config):
#         return []
#     sites = [
#         f"{config.get('Site Hierarchy', {}).get(f'sitelevel_{i+1}', f'sitelevel_{i+1}')}={value}"
#         for i, group in enumerate(locations)
#         for value in group
#     ]
#     return dmc.Accordion(
#         id="site-filters-accordion",
#         chevronPosition="right",
#         variant="separated",
#         radius="sm",
#         value=["site-filter"],
#         children=[
#             dmc.AccordionItem(
#                 value="sites-filter",
#                 children=[
#                     dmc.AccordionControl("Site Level"),
#                     dmc.AccordionPanel(
#                         pb="1rem",
#                         children=dmc.ChipGroup(
#                             id={"type": "active-filter-chip-group", "index": "site-level"},
#                             value=sites,
#                             multiple=True,
#                             children=[
#                                 dmc.Chip(
#                                     variant="outline",
#                                     icon=DashIconify(icon="bi-x-circle"),
#                                     value=value,
#                                     mt="xs",
#                                     children=value,
#                                 )
#                                 for value in sites
#                             ]
#                         )
#                     )
#                 ]
#             )
#         ]
#     )

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
        f"{key}={floor(feature_range[i], precision=2)}"
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


# @callback(
#     Output("file-filter-chips", "children"),
#     Input("umap-filter-store", "data"),
#     prevent_initial_call=True,
# )
# def update_active_file_filters(
#     file_filter_groups: Dict[int, List[str]],
# ) -> dmc.Accordion:
#     if not len(file_filter_groups):
#         return []

#     return dmc.Accordion(
#         id="active-file-filters-accordion",
#         chevronPosition="right",
#         variant="separated",
#         radius="sm",
#         children=[
#             dmc.AccordionItem(
#                 value="files-filter",
#                 children=[
#                     dmc.AccordionControl("Files"),
#                     dmc.AccordionPanel(
#                         pb="1rem",
#                         children=dmc.ChipGroup(
#                             id={"type": "active-filter-chip-group", "index": "file"},
#                             value=list(file_filter_groups.keys()),
#                             multiple=True,
#                             children=[
#                                 dmc.Chip(
#                                     variant="outline",
#                                     icon=DashIconify(icon="bi-x-circle"),
#                                     value=selection_id,
#                                     mt="xs",
#                                     children=f"UMAP Selection {selection_id}: {len(file_ids)} samples",
#                                 )
#                                 for selection_id, file_ids in file_filter_groups.items()
#                             ]
#                         )
#                     )
#                 ]
#             )
#         ]
#     )

# @callback(
#     Output("umap-filter-store", "data"),
#     State("umap-filter-store", "data"),
#     Input({"type": "active-filter-chip-group", "index": "file"}, "value"),
#     prevent_initial_call=True,
# )
# def remove_umap_selection(
#     file_filter_groups: Dict[str, List[str]],
#     values: bool,
# ) -> Dict[str, List[str]]:
#     return { value: file_filter_groups[value] for value in values }

