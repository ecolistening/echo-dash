import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import itertools
import numpy as np
import pandas as pd

from dash import callback, ctx, no_update, dcc
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch
from api import FETCH_DATASET_SITES_TREE, FETCH_DATASET_CONFIG, FETCH_DATASET_SITES_TREE, FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from api import FETCH_BASE_FILTERS, FETCH_FILES, FETCH_ACOUSTIC_FEATURES, FETCH_WEATHER, FETCH_FILE_WEATHER, FETCH_BIRDNET_SPECIES, FETCH_ACOUSTIC_FEATURES_UMAP
from api import filter_dict_to_tuples
from components.environmental_filter import EnvironmentalFilterSliderAccordion
from components.site_level_filter import SiteLevelHierarchyAccordion, TreeNodeChip
from utils.webhost import AudioAPI
from utils import ceil, floor, audio_bytes_to_enc, index_to_float, float_to_index, capitalise_each

Filters = Dict[str, Any]

def set_filters(dataset_name):
    action = FETCH_BASE_FILTERS
    payload = dict(dataset_name=dataset_name)
    filters = dispatch(action, **payload)
    filters["date_range"] = filters["date_range_bounds"]
    features = list(filters["acoustic_features"].keys())
    current_feature = filters.get("current_feature", "bioacoustic index")
    filters["current_feature"] = current_feature
    filters["current_feature_range"] = list(filters["acoustic_features"][current_feature])
    for variable in filters["weather_variables"].keys():
        filters["weather_variables"][variable]["variable_range"] = filters["weather_variables"][variable]["variable_range_bounds"]
    filters["current_sites"] = filters["tree"]
    filters["files"] = {}
    return filters

def register_callbacks():
    @callback(
        Output("filter-store", "data"),
        Input("dataset-select", "value"),
    )
    def init_dataset_filters(
        dataset_name: str,
    ) -> Filters:
        return set_filters(dataset_name)

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("filter-reset-button", "n_clicks"),
        State("dataset-select", "value"),
        prevent_initial_call=True
    )
    def reset_dataset_filters(
        n_clicks: str,
        dataset_name: str,
    ) -> Filters:
        if n_clicks == 0:
            return no_update
        return set_filters(dataset_name)

    # @callback(
    #     Output("precache", "data"),
    #     State("precache", "data"),
    #     State("dataset-select", "value"),
    #     Input("filter-store", "data"),
    # )
    # def precache_api_requests(cached_dataset: bool | None, dataset_name: str, filters: Dict[str, Any]) -> None:
    #     if not dataset_name or cached_dataset == dataset_name:
    #         return no_update

    #     logger.debug(f"{ctx.triggered_id=} caching {dataset_name} on load")
    #     payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))

    #     dispatch(FETCH_FILES, **payload)
    #     dispatch(FETCH_FILE_WEATHER, **payload)
    #     dispatch(FETCH_ACOUSTIC_FEATURES_UMAP, **payload)
    #     dispatch(FETCH_ACOUSTIC_FEATURES, **payload)
    #     dispatch(FETCH_BIRDNET_SPECIES, threshold=0.5, **payload)
    #     logger.debug(f"Filter caching {dataset_name} complete")

    #     return dataset_name

    # ------ DATES FILTER ----- #

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("date-picker", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True
    )
    def update_dates_filter_from_picker(
        selected_dates: List[str],
        filters,
    ) -> Filters:
        if selected_dates is None:
            return no_update
        if len(list(filter(None, selected_dates))) < 2:
            return no_update
        if selected_dates == filters.get("date_range", None):
            return no_update
        filters["date_range"] = selected_dates
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("date-picker-reset", "n_clicks"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def reset_dates_filter(
        n_clicks,
        filters,
    ) -> Filters:
        if n_clicks is None or n_clicks == 0:
            return no_update
        filters["date_range"] = filters["date_range_bounds"]
        return filters

    @callback(
        Output("date-picker", "minDate"),
        Output("date-picker", "maxDate"),
        Output("date-picker", "value"),
        Input("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_date_picker_from_filter(
        filters: Filters,
    ) -> Tuple[str, str, str]:
        date_range = filters["date_range"]
        min_date, max_date = filters["date_range_bounds"]
        return min_date, max_date, date_range

    @callback(
        Output("date-picker-text", "children"),
        Input("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_date_picker_text_from_filter(
        filters: Filters,
    ) -> Tuple[str, str, str]:
        min_date, max_date = filters["date_range"]
        return f"Current Range: {min_date} - {max_date}"

    # ------ ACOUSTIC FEATURE FILTER ----- #

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("feature-select", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_acoustic_feature_filter_from_select(
        selected_feature: str,
        filters,
    ) -> Filters:
        if selected_feature == filters.get("current_feature", None):
            return no_update
        selected_feature = filters["current_feature"] if not selected_feature else selected_feature
        feature_range = tuple(filters["acoustic_features"][selected_feature])
        features = list(filters["acoustic_features"].keys())
        filters["current_feature"] = selected_feature
        filters["current_feature_range"] = feature_range
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("feature-range-slider", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True
    )
    def update_acoustic_feature_filter_from_slider(
        selected_feature_range: List[float],
        filters,
    ) -> Filters:
        feature_range = filters.get("current_feature_range", [])
        feature_min, feature_max = filters["acoustic_features"][filters["current_feature"]]
        selected_feature_range = [index_to_float(x, feature_min, feature_max) for x in selected_feature_range]
        if selected_feature_range == feature_range:
            return no_update
        if selected_feature_range[0] < feature_range[0] or selected_feature_range[1] > feature_range[1]:
            return no_update
        filters["current_feature_range"] = selected_feature_range
        feature_min, feature_max = selected_feature_range
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input({"type": "active-filter-chip-group", "index": "acoustic-feature"}, "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_acoustic_feature_filter_from_chips(
        chip_values: List[str],
        filters,
    ):
        current_feature = filters["current_feature"]
        feature_min, feature_max = filters["acoustic_features"][current_feature]
        selected_values = {prefix: float(value) for prefix, value in map(lambda s: s.split("="), chip_values)}
        feature_range = [selected_values.get("start_value", feature_min), selected_values.get("end_value", feature_max)]
        if feature_range == filters.get("current_feature_range"):
            return no_update
        filters["current_feature_range"] = feature_range
        return filters

    @callback(
        Output("feature-select", "value"),
        Output("feature-select", "data"),
        Input("filter-store", "data")
    )
    def update_acoustic_feature_select(
        filters: Filters
    ) -> Tuple[str, List[str]]:
        return filters["current_feature"], [
            dict(value=feature, label=capitalise_each(feature))
            for feature  in list(filters["acoustic_features"].keys())
        ]

    @callback(
        Output("feature-range-slider", "value"),
        Output("feature-range-slider", "marks"),
        Output("feature-range-title", "children"),
        Input("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_acoustic_feature_slider(
        filters: Filters
    ) -> Tuple[str, List[str]]:
        feature_range = filters["current_feature_range"]
        current_feature = filters["current_feature"]
        feature_bounds = filters["acoustic_features"][current_feature]
        feature_min, feature_max = feature_bounds
        range_description = f"{feature_min} - {feature_max}"
        marks = [
            dict(value=0, label=str(floor(feature_min, precision=2))),
            dict(value=999, label=str(ceil(feature_max, precision=2)))
        ]
        values = [float_to_index(val, feature_min, feature_max) for val in feature_range]
        return values, marks, f"Acoustic Feature Range: {floor(feature_range[0], precision=2)} - {ceil(feature_range[1], precision=2)}"

    # ------ WEATHER FILTER ----- #

    @callback(
        Output("weather-variable-filter-groups", "children"),
        Input("dataset-select", "value"),
    )
    def init_weather_filters(
        dataset_name: str
    ) -> List[dmc.Box]:
        action = FETCH_DATASET_DROPDOWN_OPTION_GROUPS
        payload = dict(
            dataset_name=dataset_name,
            options=("Temperature", "Precipitation", "Wind"),
            default=[],
        )
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        opt_groups = dispatch(action, **payload)
        return [
            EnvironmentalFilterSliderAccordion(**opt_group)
            for opt_group in opt_groups
        ]

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input({"type": "weather-variable-range-slider", "index": ALL}, "value"),
        State({"type": "weather-variable-range-slider", "index": ALL}, "id"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_weather_filter(
        slider_values: List[str],
        slider_ids: List[str],
        filters: Filters,
    ) -> Filters:
        if not ctx.triggered_id:
            return no_update
        variable_name = ctx.triggered_id["index"]
        variable_params = filters["weather_variables"][variable_name]
        ids, values = slider_ids, slider_values
        context = [(id["index"], current_range) for id, current_range in zip(ids, values) if id["index"] == variable_name]
        if not len(context):
            return no_update
        _, current_range = context[0]
        if current_range == None or not len(list(filter(None, current_range))):
            return no_update
        min_val, max_val = variable_params["variable_range_bounds"]
        current_range = [index_to_float(x, min_val, max_val) for x in current_range]
        if current_range == variable_params["variable_range"]:
            return no_update
        filters["weather_variables"][variable_name]["variable_range"] = current_range
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input({"type": "weather-variable-reset", "index": ALL}, "n_clicks"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def reset_weather_filter(
        reset_clicks: List[str],
        filters: Filters,
    ) -> Filters:
        if not len(list(filter(None, reset_clicks))):
            return no_update
        variable_name = ctx.triggered_id["index"]
        variable_params = filters["weather_variables"][variable_name]
        filters["weather_variables"][variable_name]["variable_range"] = variable_params["variable_range_bounds"]
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("weather-filter-reset-all", "n_clicks"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def reset_weather_filter(
        reset_clicks: List[str],
        filters: Filters,
    ) -> Filters:
        if not reset_clicks:
            return no_update
        for variable_name, params in filters["weather_variables"].items():
            filters["weather_variables"][variable_name]["variable_range"] = params["variable_range_bounds"]
        return filters

    @callback(
        Output({"type": "weather-variable-range-slider", "index": ALL}, "value"),
        Input("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_weather_variable_slider(
        filters: Filters
    ) -> Tuple[str, List[str]]:
        current_filter_values = list(map(
            lambda params: params["variable_range"],
            filters["weather_variables"].values()
        ))
        variable_bounds = list(map(
            lambda params: params["variable_range_bounds"],
            filters["weather_variables"].values()
        ))
        idx = []
        for vals, bounds in zip(current_filter_values, variable_bounds):
            min_val, max_val = bounds
            idx.append([float_to_index(x, min_val, max_val) for x in vals])
        return idx

    @callback(
        Output({"type": "weather-variable-range-text", "index": ALL}, "children"),
        Input("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_weather_variable_slider(
        filters: Filters
    ) -> Tuple[str, List[str]]:
        current_filter_values = list(map(
            lambda params: params["variable_range"],
            filters["weather_variables"].values()
        ))
        values = []
        for minimum, maximum in current_filter_values:
            values.append(f"Current Range: {minimum} - {maximum}")
        return values

    # ------ SITE LEVEL FILTER ----- #

    @callback(
        Output("site-level-filter-group", "children"),
        Input("dataset-select", "value"),
    )
    def init_site_level_filters(
        dataset_name: str,
    ) -> dmc.Stack:
        action = FETCH_DATASET_SITES_TREE
        payload = dict(dataset_name=dataset_name)
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        tree = dispatch(action, **payload)

        action = FETCH_DATASET_CONFIG
        payload = dict(dataset_name=dataset_name)
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        config = dispatch(action, **payload)
        return SiteLevelHierarchyAccordion(tree=tree, config=config.get("Site Hierarchy"))

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
        State("filter-store", "data"),
        State("dataset-select", "value"),
        prevent_initial_call=True,
    )
    def update_site_level_filter(
        values: List[str],
        filters: Filters,
        dataset_name: str,
    ) -> Filters:
        flat_values = list(itertools.chain(*values))
        # this shouldn't happen, but a guard will prevent bugs
        if not len(flat_values):
            return no_update
        # when nodes haven't changed, prevent update to stop graph reload triggering
        current_nodes = [node.path_name for node in bt.list_to_tree(filters["current_sites"]).descendants]
        if sorted(current_nodes) == sorted(flat_values):
            return no_update

        action = FETCH_DATASET_SITES_TREE
        payload = dict(dataset_name=dataset_name)
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        tree = dispatch(action, **payload)
        # find child nodes at specified depth
        depth = ctx.triggered_id["index"]
        nodes = bt.levelorder_iter(tree, filter_condition=lambda node: node.depth == depth + 2)
        # remove all nodes where the parent is not present in selected values
        nodes = filter(lambda node: node.parent and node.parent.path_name in flat_values, nodes)
        nodes = sorted(nodes, key=lambda node: node.path_name)
        # recursively build out child list using each preserved child node
        children = [list(bt.tree_to_dict(node).keys()) for node in nodes]
        # preserve tree up to depth, rebuild children based on filtering
        values = values[:depth] + children
        filters["current_sites"] = list(itertools.chain(*values))
        return filters

    @callback(
        Output({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
        Input("filter-store", "data"),
        State({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
        State("dataset-select", "value"),
        prevent_initial_call=True,
    )
    def update_site_level_filters(
        filters: str,
        current_sites,
        dataset_name: str,
    ) -> Tuple[List[TreeNodeChip], List[str]]:
        # FIXME: to prevent exception when changing dataaset, we should return the node chip rather than its values
        # as the number of site chips may have changed
        sites = filters["current_sites"]

        payload = dict(dataset_name=dataset_name)
        tree = dispatch(FETCH_DATASET_SITES_TREE, **payload)
        config = dispatch(FETCH_DATASET_CONFIG, **payload)

        values = []
        if not len(sites):
            # if all sites have been de-selected, re-select all of them
            for depth in range(1, tree.max_depth):
                nodes = sorted(bt.levelorder_iter(tree, filter_condition=lambda node: node.depth == depth + 1), key=lambda node: node.path_name)
                values.append([node.path_name for node in nodes])
        else:
            # otherwise return only the values of selected sites
            current_tree = bt.list_to_tree(sites)
            for depth in range(1, tree.max_depth):
                condition = lambda node: node.depth == depth + 1
                nodes = sorted(bt.levelorder_iter(tree, filter_condition=condition), key=lambda node: node.path_name)
                values.append([node.path_name for node in nodes if bool(bt.find_full_path(current_tree, node.path_name))])
        return values

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        State("filter-store", "data"),
        Input("site-filter-reset", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_site_level_filters(
        filters: str,
        current_sites,
    ) -> Tuple[List[TreeNodeChip], List[str]]:
        filters["current_sites"] = filters["tree"]
        return filters

    # ------- FILE ID FILTER ------ #

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input({"type": "active-filter-chip-group", "index": "file"}, "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def remove_umap_selection(
        values: bool,
        filters: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        file_filters = filters["files"]
        # remove by index
        filters["files"] = {value: file_filters[value] for value in values}
        return filters

    # ---- DUMP ---- #

    # @callback(
    #     Output("site-filter-chips", "children"),
    #     Input("filter-store", "data"),
    #     State("dataset-select", "value"),
    #     Input("dataset-config", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_active_site_filters(
    #     filters: List[str],
    #     dataset_name: str,
    #     config: Dict[str, Dict[str, str]],
    # ) -> dmc.Accordion:
    #     action = FETCH_DATASET_SITES_TREE
    #     payload = dict(dataset_name=dataset_name)
    #     logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    #     tree = dispatch(action, **payload)

    #     site_hierarchy = config.get("Site Hierarchy", {})
    #     active_sites = filters["current_sites"]
    #     absent_sites = []
    #     for depth in range(1, tree.max_depth):
    #         condition = lambda node: node.depth == depth + 1
    #         nodes = sorted(bt.levelorder_iter(tree, filter_condition=condition), key=lambda node: node.path_name)
    #         nodes = filter(lambda node: node.path_name not in active_sites, nodes)
    #         absent_sites.append([node.path_name for node in nodes])
    #     return dmc.Accordion(
    #         id="site-filters-accordion",
    #         chevronPosition="right",
    #         variant="separated",
    #         radius="sm",
    #         persistence=True,
    #         children=[
    #             dmc.AccordionItem(
    #                 value="sites-filter",
    #                 children=[
    #                     dmc.AccordionControl("Site Level"),
    #                     dmc.AccordionPanel(
    #                         pb="1rem",
    #                         children=[
    #                             dmc.Box([
    #                                 dmc.Space(h="sm"),
    #                                 dmc.Text(
    #                                     children=site_hierarchy.get(f'sitelevel_{depth + 1}', f'site_level_{depth + 1}'),
    #                                     size="sm",
    #                                 ),
    #                                 dmc.ChipGroup(
    #                                     id={"type": "active-filter-chip-group", "index": "site-level"},
    #                                     value=values,
    #                                     multiple=True,
    #                                     children=[
    #                                         dmc.Chip(
    #                                             variant="outline",
    #                                             icon=DashIconify(icon="bi-x-circle"),
    #                                             value=value,
    #                                             children=value,
    #                                         )
    #                                         for value in values
    #                                     ],
    #                                 ),
    #                             ])
    #                             for depth, values in enumerate(absent_sites)
    #                         ]
    #                     )
    #                 ]
    #             )
    #         ]
    #     )

    # @callback(
    #     Output("file-filter-chips", "children"),
    #     Input("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_active_file_filters(
    #     filters: Dict[int, List[str]],
    # ) -> dmc.Accordion:
    #     file_filters = filters["files"]
    #     if not len(file_filters):
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
    #                             value=list(file_filters.keys()),
    #                             multiple=True,
    #                             children=[
    #                                 dmc.Chip(
    #                                     variant="outline",
    #                                     icon=DashIconify(icon="bi-x-circle"),
    #                                     value=selection_id,
    #                                     mt="xs",
    #                                     children=f"UMAP Selection {selection_id}: {len(file_ids)} samples",
    #                                 )
    #                                 for selection_id, file_ids in file_filters.items()
    #                             ]
    #                         )
    #                     )
    #                 ]
    #             )
    #         ]
    #     )


    # @callback(
    #     Output("date-range-filter-chips", "children"),
    #     Input("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_date_filter_chips(
    #     filters: Filters,
    # ) -> dmc.Accordion:
    #     selected_dates = filters["date_range"]
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
    #         persistence=True,
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
    #     Output("weather-variable-filter-chips", "children"),
    #     Input("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_weather_filter_chips(
    #     filters: Filters,
    # ) -> dmc.Accordion:
    #     return dmc.Accordion(
    #         id="active-weather-variable-filters-accordion",
    #         chevronPosition="right",
    #         variant="separated",
    #         radius="sm",
    #         persistence=True,
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
    #                                     children=variable_name,
    #                                     size="sm",
    #                                 ),
    #                                 dmc.Space(h="sm"),
    #                                 dmc.ChipGroup(
    #                                     id={"type": "weather-variable-chip-group", "index": variable_name },
    #                                     value=list(map(lambda s: "=".join(map(str, s)), zip(["start_value", "end_value"], variable_params["variable_range"]))),
    #                                     multiple=True,
    #                                     children=[
    #                                         dmc.Chip(
    #                                             variant="outline",
    #                                             icon=DashIconify(icon="bi-x-circle"),
    #                                             value=f"{suffix}={value}",
    #                                             mt="xs",
    #                                             children=f"{suffix}={value}",
    #                                         )
    #                                         for suffix, value in zip(["start_value", "end_value"], variable_params["variable_range"])
    #                                     ],
    #                                 ),
    #                             ])
    #                             for variable_name, variable_params in filters["weather_variables"].items()
    #                         ]
    #                     )
    #                 ]
    #             )
    #         ]
    #     )


    # @callback(
    #     Output("filter-store", "data", allow_duplicate=True),
    #     Input({"type": "weather-variable-chip-group", "index": ALL}, "value"),
    #     State({"type": "weather-variable-chip-group", "index": ALL}, "id"),
    #     State("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_weather_filter(
    #     chip_values: List[str],
    #     chip_ids: List[str],
    #     filters: Filters,
    # ) -> Filters:
    #     if not ctx.triggered_id:
    #         return no_update
    #     variable_name = ctx.triggered_id["index"]
    #     variable_params = filters["weather_variables"][variable_name]
    #     ids, values = chip_ids, chip_values
    #     context = [(id["index"], current_range) for id, current_range in zip(ids, values) if id["index"] == variable_name]
    #     if not len(context):
    #         return no_update
    #     _, current_range = context[0]
    #     selected_values = {prefix: float(value) for prefix, value in map(lambda s: s.split("="), current_range)}
    #     variable_min, variable_max = variable_params["variable_range_bounds"]
    #     current_range = [selected_values.get("start_value", variable_min), selected_values.get("end_value", variable_max)]
    #     update = current_range != variable_params['variable_range']
    #     if not update:
    #         return no_update
    #     filters["weather_variables"][variable_name]["variable_range"] = current_range
    #     return filters

    # @callback(
    #     Output("acoustic-feature-range-filter-chips", "children"),
    #     Input("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_acoustic_range_filter_chips(
    #     filters,
    # ) -> dmc.Accordion:
    #     feature = filters["current_feature"]
    #     feature_range = filters["current_feature_range"]
    #     feature_range = [
    #         f"{key}={feature_range[i]}"
    #         for i, key in enumerate(["start_value", "end_value"])
    #     ]
    #     return dmc.Accordion(
    #         id="active-acoustic-range-filters-accordion",
    #         chevronPosition="right",
    #         variant="separated",
    #         persistence=True,
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
    #                                 children=feature,
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
    #     Output("filter-store", "data", allow_duplicate=True),
    #     Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
    #     State("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # def update_dates_filter_from_chips(
    #     chip_values: List[str],
    #     filters,
    # ) -> Filters:
    #     min_date, max_date = filters["date_range_bounds"]
    #     dates_dict = {prefix: date for prefix, date in map(lambda s: s.split("="), chip_values)}
    #     date_range = [dates_dict.get("start_date", min_date), dates_dict.get("end_date", max_date)]
    #     if date_range == filters.get("date_range", None):
    #         return no_update
    #     filters["date_range"] = date_range
    #     return filters

