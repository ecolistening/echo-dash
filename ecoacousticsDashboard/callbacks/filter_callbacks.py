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

from api import (
    dispatch,
    FETCH_DATASET_SITES_TREE,
    FETCH_DATASET_CONFIG,
    FETCH_DATASET_SITES_TREE,
    FETCH_FILES,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_WEATHER,
    FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
)
from components.environmental_filter import EnvironmentalFilterSliderAccordion
from components.site_level_filter import SiteLevelHierarchyAccordion, TreeNodeChip
from utils import ceil, floor

Filters = Dict[str, Any]

def register_callbacks():
    @callback(
        Output("filter-store", "data"),
        Input("dataset-select", "value"),
        State("filter-store", "data"),
    )
    def init_dataset_filters(
        dataset_name: str,
        filters: Filters,
    ) -> Filters:
        filters = {} if filters is None else filters
        params = dict(dataset_name=dataset_name)
        filters["current_dataset"] = dataset_name
        # set dates and date range
        data = dispatch(FETCH_FILES, **params)
        min_date = data.timestamp.dt.date.min().strftime("%Y-%m-%d")
        max_date = data.timestamp.dt.date.max().strftime("%Y-%m-%d")
        date_range = [min_date, max_date]
        filters["date_range_bounds"] = date_range
        filters["date_range"] = date_range
        # set feature and feature range
        data = dispatch(FETCH_ACOUSTIC_FEATURES, **params)
        features = data["feature"].unique()
        current_feature = filters.get("current_feature", features[0])
        feature_data = data.loc[data["feature"] == current_feature, "value"]
        feature_min = floor(feature_data.min(), precision=2)
        feature_max = ceil(feature_data.max(), precision=2)
        acoustic_features = {}
        for feature in features:
            df = data.loc[data["feature"] == feature, "value"]
            acoustic_features[feature] = [floor(df.min(), precision=2), ceil(df.max(), precision=2)]
        filters["acoustic_features"] = acoustic_features
        filters["current_feature"] = current_feature
        filters["current_feature_range"] = list(filters["acoustic_features"][current_feature])
        # set weather variables and default ranges
        data = dispatch(FETCH_WEATHER, **params)
        weather_variables = {}
        for variable in data.variable.unique():
            df = data.loc[data["variable"] == variable, "value"]
            variable_ranges = {}
            variable_range = [floor(df.min()), ceil(df.max())]
            variable_ranges["variable_range_bounds"] = variable_range
            variable_ranges["variable_range"] = variable_range
            weather_variables[variable] = variable_ranges
        filters["weather_variables"] = weather_variables
        # set site filters
        root_node = dispatch(FETCH_DATASET_SITES_TREE, **params)
        sites = list(bt.tree_to_dict(root_node).keys())[1:]
        filters["current_sites"] = sites
        # file filters defaults to empty
        filters["files"] = {}
        logger.debug(filters)
        return filters

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
    ):
        if selected_dates is not None and len(list(filter(None, selected_dates))) < 2:
            return no_update
        if selected_dates == filters.get("date_range", None):
            return no_update
        filters["date_range"] = selected_dates
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_dates_filter_from_chips(
        chip_values: List[str],
        filters,
    ):
        min_date, max_date = filters["date_range_bounds"]
        dates_dict = {prefix: date for prefix, date in map(lambda s: s.split("="), chip_values)}
        date_range = [dates_dict.get("start_date", min_date), dates_dict.get("end_date", max_date)]
        if date_range == filters.get("date_range", None):
            return no_update
        filters["date_range"] = date_range
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

    # ------ ACOUSTIC FEATURE FILTER ----- #

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Input("feature-select", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True
    )
    def update_acoustic_feature_filter_from_select(
        selected_feature: str,
        filters,
    ):
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
    ):
        if selected_feature_range == filters.get("current_feature_range", None):
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
        Output("acoustic-feature-range-filter-chips", "children"),
        Input("filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_acoustic_range_filter_chips(
        filters,
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

    # ------ WEATHER FILTER ----- #

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


    # ------ SITE LEVEL FILTER ----- #


    @callback(
        Output("site-level-filter-group", "children"),
        Input("dataset-select", "value"),
        Input("dataset-config", "data"),
    )
    def init_site_level_filters(
        dataset_name: str,
        config: Dict[str, str],
    ) -> dmc.Stack:
        tree = dispatch(FETCH_DATASET_SITES_TREE, dataset_name=dataset_name)
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
        current_tree = bt.list_to_tree(filters["current_sites"])
        # when nodes haven't changed, prevent update to stop graph reload triggering
        current_nodes = sorted([node.path_name for node in current_tree.descendants])
        if current_nodes == flat_values:
            return no_update
        tree = dispatch(FETCH_DATASET_SITES_TREE, dataset_name=dataset_name)
        # find child nodes at specified depth
        depth = ctx.triggered_id["index"]
        nodes = bt.levelorder_iter(tree, filter_condition=lambda node: node.depth == len(values[depth:]) + 1)
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
        State("dataset-select", "value"),
        Input("dataset-config", "data"),
        prevent_initial_call=True,
    )
    def update_site_level_filters(
        filters: str,
        dataset_name: str,
        config: Dict[str, str]
    ) -> Tuple[List[TreeNodeChip], List[str]]:
        tree = dispatch(FETCH_DATASET_SITES_TREE, dataset_name=dataset_name)
        config = config.get("Site Hierarchy", {})
        sites = filters["current_sites"]
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
        Output("site-filter-chips", "children"),
        Input("filter-store", "data"),
        State("dataset-select", "value"),
        Input("dataset-config", "data"),
        prevent_initial_call=True,
    )
    def update_active_site_filters(
        filters: List[str],
        dataset_name: str,
        config: Dict[str, Dict[str, str]],
    ) -> dmc.Accordion:
        tree = dispatch(FETCH_DATASET_SITES_TREE, dataset_name=dataset_name)
        site_hierarchy = config.get("Site Hierarchy", {})
        active_sites = filters["current_sites"]
        absent_sites = []
        for depth in range(1, tree.max_depth):
            condition = lambda node: node.depth == depth + 1
            nodes = sorted(bt.levelorder_iter(tree, filter_condition=condition), key=lambda node: node.path_name)
            nodes = filter(lambda node: node.path_name not in active_sites, nodes)
            absent_sites.append([node.path_name for node in nodes])
        return dmc.Accordion(
            id="site-filters-accordion",
            chevronPosition="right",
            variant="separated",
            radius="sm",
            value=["site-filter"],
            children=[
                dmc.AccordionItem(
                    value="sites-filter",
                    children=[
                        dmc.AccordionControl("Site Level"),
                        dmc.AccordionPanel(
                            pb="1rem",
                            children=[
                                dmc.Box([
                                    dmc.Space(h="sm"),
                                    dmc.Text(
                                        children=site_hierarchy.get(f'sitelevel_{depth + 1}', f'site_level_{depth + 1}'),
                                        size="sm",
                                    ),
                                    dmc.ChipGroup(
                                        id={"type": "active-filter-chip-group", "index": "site-level"},
                                        value=values,
                                        multiple=True,
                                        children=[
                                            dmc.Chip(
                                                variant="outline",
                                                icon=DashIconify(icon="bi-x-circle"),
                                                value=value,
                                                children=value,
                                            )
                                            for value in values
                                        ],
                                    ),
                                ])
                                for depth, values in enumerate(absent_sites)
                            ]
                        )
                    ]
                )
            ]
        )


    # ------- FILE ID FILTER ------ #

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
