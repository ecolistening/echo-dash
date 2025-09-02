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
    Output("filter-store", "data"),
    Input("dataset-select", "value"),
    State("filter-store", "data"),
)
def init_filter_store(
    dataset_name: str,
    filters: Dict[str, Any],
) -> Dict[str, Any]:
    data = dispatch(FETCH_FILES, dataset_name=dataset_name)
    filters["date_range"] = (data.timestamp.dt.date.min(), data.timestamp.dt.date.max())
    filters["date_range_bounds"] = tuple(filters["date_range"])
    data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
    features = data["feature"].unique()
    filters["acoustic_features"] = {}
    for feature in features:
        df = data.loc[data["feature"] == feature, "value"]
        filters["acoustic_features"][feature] = (floor(df.min(), precision=2), ceil(df.max(), precision=2))
    current_feature = features[0]
    filters["current_feature"] = current_feature
    filters["current_feature_range"] = tuple(filters["acoustic_features"][current_feature])
    logger.debug(filters)
    return filters

@callback(
    Output("feature-select", "value"),
    Output("feature-select", "data"),
    Output("feature-range-slider", "min"),
    Output("feature-range-slider", "max"),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def init_feature_select_range(dataset_name: str):
    data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
    features = data["feature"].unique()
    current_feature = features[0]
    feature_data = data.loc[data["feature"] == current_feature, "value"]
    feature_min = floor(feature_data.min(), precision=2)
    feature_max = ceil(feature_data.max(), precision=2)
    return current_feature, features, feature_min, feature_max

@callback(
    Output("filter-store", "data", allow_duplicate=True),
    Output("feature-range-slider", "value"),
    Output("feature-range-slider", "min"),
    Output("feature-range-slider", "max"),
    Input("feature-select", "value"),
    State("filter-store", "data"),
    prevent_initial_call=True,
)
def update_current_feature(feature: str, filters: Dict[str, Any]):
    logger.debug(feature, filters)
    filters["current_feature"] = feature
    feature_range = filters["acoustic_features"][feature]
    return filters, feature_range, feature_range[0], feature_range[1]

@callback(
    Output("feature-range-bounds", "children"),
    Input("feature-range-slider", "value"),
    prevent_initial_call=True,
)
def update_description_text_from_slider(
    values: List[float],
) -> str:
    selected_min, selected_max = values
    return f"{selected_min} - {selected_max}"

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def init_date_picker(dataset_name: str):
    data = dispatch(FETCH_FILES, dataset_name=dataset_name)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    values = (min_date, max_date)
    return min_date, max_date, values

@callback(
    Output("filter-store", "data", allow_duplicate=True),
    Input("date-picker", "value"),
    State("filter-store", "data"),
    prevent_initial_call=True,
)
def update_current_date_range(selected_dates: str, filters: Dict[str, Any]):
    if selected_dates is None or len(list(filter(None, selected_dates))) < 2:
        return no_update
    filters["date_range"] = selected_dates
    return filters

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


# @callback(
#     Output("date-range-filter-chips", "children"),
#     Input("date-range-current-bounds", "data"),
#     prevent_initial_call=True,
# )
# def update_active_date_filters(
#     selected_dates: List[str],
# ) -> dmc.Accordion:
#     if not len(selected_dates):
#         return []
#     date_range = [
#         f"{key}={selected_dates[i]}"
#         for i, key in enumerate(["start_date", "end_date"])
#     ]
#     return dmc.Accordion(
#         id="date-range-filters-accordion",
#         chevronPosition="right",
#         variant="separated",
#         radius="sm",
#         value=["dates-filter"],
#         children=[
#             dmc.AccordionItem(
#                 value="dates-filter",
#                 children=[
#                     dmc.AccordionControl("Date Range"),
#                     dmc.AccordionPanel(
#                         pb="1rem",
#                         children=dmc.ChipGroup(
#                             id={"type": "active-filter-chip-group", "index": "date-range"},
#                             value=date_range,
#                             multiple=True,
#                             children=[
#                                 dmc.Chip(
#                                     variant="outline",
#                                     icon=DashIconify(icon="bi-x-circle"),
#                                     value=value,
#                                     mt="xs",
#                                     children=value,
#                                 )
#                                 for value in date_range
#                             ]
#                         )
#                     )
#                 ]
#             )
#         ]
#     )

# @callback(
#     Output("acoustic-feature-range-filter-chips", "children"),
#     Input("acoustic-feature-current-bounds", "data"),
#     prevent_initial_call=True,
# )
# def update_active_acoustic_range_filters(
#     state: Dict[str, Any],
# ) -> dmc.Accordion:
#     feature_range = [
#         f"{key}={floor(state[key], precision=2)}"
#         for key in ["start_value", "end_value"]
#     ]
#     return dmc.Accordion(
#         id="active-acoustic-range-filters-accordion",
#         chevronPosition="right",
#         variant="separated",
#         value=["acoustic-range-filter"],
#         radius="sm",
#         children=[
#             dmc.AccordionItem(
#                 value="acoustic-range-filter",
#                 children=[
#                     dmc.AccordionControl("Acoustic Feature Range"),
#                     dmc.AccordionPanel(
#                         pb="1rem",
#                         children=[
#                             dmc.Text(
#                                 children=state["feature"],
#                                 size="sm",
#                             ),
#                             dmc.Space(h="sm"),
#                             dmc.ChipGroup(
#                                 id={"type": "active-filter-chip-group", "index": "acoustic-feature"},
#                                 value=feature_range,
#                                 multiple=True,
#                                 children=[
#                                     dmc.Chip(
#                                         variant="outline",
#                                         icon=DashIconify(icon="bi-x-circle"),
#                                         value=value,
#                                         mt="xs",
#                                         children=value,
#                                     )
#                                     for value in feature_range
#                                 ]
#                             ),
#                         ]
#                     )
#                 ]
#             )
#         ]
#     )

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

# @callback(
#     Output("date-range-current-bounds", "data", allow_duplicate=True),
#     State("date-range-store", "data"),
#     Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
#     prevent_initial_call=True,
# )
# def reset_date_range_selection(
#     current_date_store: Dict[str, dt.date],
#     values: List[str],
# ) -> Dict[str, dt.date]:
#     selected_dates = {}
#     for value in values:
#         prefix, date_str = value.split("=")
#         selected_dates[prefix] = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
#     return [
#         selected_dates.get("start_date", dt.datetime.strptime(current_date_store["min"], "%Y-%m-%d").date()),
#         selected_dates.get("end_date", dt.datetime.strptime(current_date_store["max"], "%Y-%m-%d").date()),
#     ]

# @callback(
#     Output("acoustic-feature-current-bounds", "data", allow_duplicate=True),
#     State("acoustic-feature-store", "data"),
#     State("acoustic-feature-current-bounds", "data"),
#     Input({"type": "active-filter-chip-group", "index": "acoustic-feature"}, "value"),
#     prevent_initial_call=True,
# )
# def reset_acoustic_feature_range_selection(
#     store: Dict[str, Any],
#     state: Dict[str, Any],
#     values: List[str],
# ) -> Dict[str, Any]:
#     selected_values = {}
#     for value in values:
#         prefix, value = value.split("=")
#         selected_values[prefix] = float(value)
#     feature = state["feature"]
#     return {
#         "feature": feature,
#         "start_value": selected_values.get("start_value", store[feature]["min"]),
#         "end_value": selected_values.get("end_value", store[feature]["max"]),
#     }
