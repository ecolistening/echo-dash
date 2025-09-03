import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import callback, ctx, no_update
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_DATASETS, FETCH_FILES, FETCH_ACOUSTIC_FEATURES
from utils import ceil, floor

@callback(
    Output("feature-select", "value"),
    Output("feature-select", "data"),
    Output("feature-range-slider", "min"),
    Output("feature-range-slider", "max"),
    Output("feature-range-slider", "value"),
    Output("feature-range-bounds", "children"),
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Output("filter-store", "data"),
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input("feature-select", "value"),
    Input("feature-range-slider", "value"),
    State("filter-store", "data"),
)
def update_filters(
    dataset_name: str,
    selected_dates: List[str],
    selected_feature: str,
    selected_feature_range: List[float],
    filters: Dict[str, Any],
):
    logger.debug(filters)
    filters = {} if filters is None else filters
    # if setting dataset
    if ctx.triggered_id == "dataset-select":
        # reset dates and date range
        data = dispatch(FETCH_FILES, dataset_name=dataset_name)
        min_date = data.timestamp.dt.date.min()
        max_date = data.timestamp.dt.date.max()
        date_range = (min_date, max_date)
        filters["date_range_bounds"] = date_range
        filters["date_range"] = date_range
        # reset feature and feature range
        data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
        features = data["feature"].unique()
        current_feature = selected_feature or features[0]
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
        selected_feature_range = tuple(filters["acoustic_features"][current_feature])
        range_description = f"{feature_min} - {feature_max}"
        return (
            current_feature, features, feature_min, feature_max, selected_feature_range, range_description,
            min_date, max_date, date_range,
            filters,
        )
    # if changing dates
    if ctx.triggered_id == "date-picker":
        if selected_dates is not None and len(list(filter(None, selected_dates))) < 2:
            # THE HORROR
            return (
                no_update, no_update, no_update, no_update, no_update, no_update,
                no_update, no_update, no_update,
                filters,
            )
        min_date, max_date = filters["date_range_bounds"]
        filters["date_range"] = selected_dates
        return (
            no_update, no_update, no_update, no_update, no_update, no_update,
            min_date, max_date, selected_dates,
            filters
        )
    # if changing feature
    if ctx.triggered_id == "feature-select":
        selected_feature = filters["current_feature"] if not selected_feature else selected_feature
        feature_range = tuple(filters["acoustic_features"][selected_feature])
        features = list(filters["acoustic_features"].keys())
        feature_min, feature_max = feature_range
        filters["current_feature"] = selected_feature
        filters["current_feature_range"] = feature_range
        range_description = f"{feature_min} - {feature_max}"
        return (
            selected_feature, features, feature_min, feature_max, feature_range, range_description,
            no_update, no_update, no_update,
            filters,
        )
    # if changing feature range
    if ctx.triggered_id == "feature-range-slider":
        filters["current_feature_range"] = selected_feature_range
        feature_min, feature_max = selected_feature_range
        range_description = f"{feature_min} - {feature_max}"
        return (
            no_update, no_update, no_update, no_update, selected_feature_range, range_description,
            no_update, no_update, no_update,
            filters,
        )
    return (
        no_update, no_update, no_update, no_update, no_update, no_update,
        no_update, no_update, no_update,
        filters,
    )

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
    Output("date-picker", "value", allow_duplicate=True),
    Output("filter-store", "data", allow_duplicate=True),
    Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
    State("filter-store", "data"),
    prevent_initial_call=True,
)
def reset_active_date_filters(
    values: List[str],
    filters: Dict[str, Any],
) -> Dict[str, dt.date]:
    min_date, max_date = filters["date_range_bounds"]
    selected_dates = {}
    for value in values:
        prefix, date_str = value.split("=")
        selected_dates[prefix] = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    date_range = [
        selected_dates.get("start_date", dt.datetime.strptime(min_date, "%Y-%m-%d").date()),
        selected_dates.get("end_date", dt.datetime.strptime(max_date, "%Y-%m-%d").date()),
    ]
    filters["date_range"] = date_range
    return date_range, filters

@callback(
    Output("feature-range-slider", "value", allow_duplicate=True),
    Output("feature-range-bounds", "children", allow_duplicate=True),
    Output("filter-store", "data", allow_duplicate=True),
    Input({"type": "active-filter-chip-group", "index": "acoustic-feature"}, "value"),
    State("filter-store", "data"),
    prevent_initial_call=True,
)
def reset_active_feature_filters(
    values: List[str],
    filters: Dict[str, Any],
) -> Dict[str, dt.date]:
    current_feature = filters["current_feature"]
    feature_min, feature_max = filters["acoustic_features"][current_feature]
    selected_values = {}
    for value in values:
        prefix, value = value.split("=")
        selected_values[prefix] = float(value)
    feature_range = [
        selected_values.get("start_value", feature_min),
        selected_values.get("end_value", feature_max),
    ]
    filters["current_feature_range"] = feature_range
    range_description = f"{feature_min} - {feature_max}"
    return feature_range, range_description, filters

@callback(
    Output("date-range-filter-chips", "children"),
    Input("filter-store", "data"),
    prevent_initial_call=True,
)
def update_active_date_filters(
    filters: List[str],
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
def update_active_acoustic_range_filters(
    filters: Dict[str, Any],
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
#     Output("weather-variable-filter-chips", "children"),
#     Input({"type": "weather-variable-range-slider", "index": ALL}, "id"),
#     Input({"type": "weather-variable-range-slider", "index": ALL}, "value"),
#     prevent_initial_call=True,
# )
# def update_active_weather_filters(
#     weather_variables: List[List[str]],
#     weather_ranges: List[List[float]],
# ) -> dmc.Accordion:
#     weather_params = dict(zip(
#         map(lambda match: match["index"], weather_variables),
#         map(tuple, weather_ranges)
#     ))
#     return dmc.Accordion(
#         id="active-weather-variable-filters-accordion",
#         chevronPosition="right",
#         variant="separated",
#         radius="sm",
#         value=["weather-variable-filter"],
#         children=[
#             dmc.AccordionItem(
#                 value="weather-variable-filter",
#                 children=[
#                     dmc.AccordionControl("Environmental"),
#                     dmc.AccordionPanel(
#                         pb="1rem",
#                         children=[
#                             dmc.Box([
#                                 dmc.Space(h="sm"),
#                                 dmc.Text(
#                                     children=weather_variable,
#                                     size="sm",
#                                 ),
#                                 dmc.Space(h="sm"),
#                                 dmc.ChipGroup(
#                                     id={"type": "weather-variable-chip-group", "index": weather_variable},
#                                     value=variable_range,
#                                     multiple=True,
#                                     children=[
#                                         dmc.Chip(
#                                             variant="outline",
#                                             icon=DashIconify(icon="bi-x-circle"),
#                                             value=value,
#                                             mt="xs",
#                                             children=f"{suffix}={value}",
#                                         )
#                                         for suffix, value in zip(["start_value", "end_value"], variable_range)
#                                     ],
#                                 ),
#                             ])
#                             for weather_variable, variable_range in weather_params.items()
#                         ]
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

