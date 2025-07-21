import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import itertools
import numpy as np

from dash import callback, Output, Input, State, ALL, ctx, no_update
from loguru import logger
from typing import Any, Dict, List, Tuple

from components.site_level_filter import SiteLevelHierarchyAccordion, TreeNodeChip
from utils import floor, ceil

from api import (
    dispatch,
    FETCH_DATASET_SITES_TREE,
    FETCH_DATASET_CONFIG,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_FILES,
)


SITE_HIERARCHY_KEY = "Site Hierarchy"

@callback(
    Output("feature-dropdown", "value"),
    Output("feature-dropdown", "data"),
    Input("dataset-select", "value"),
    State("acoustic-feature-store", "data"),
)
def set_acoustic_feature_dropdown(
    dataset_name: str,
    store: str | None = None,
) -> Tuple[str, List[str], float, float]:
    data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
    feature_names = data["feature"].unique()
    feature = store.get("feature", feature_names[0])
    return feature, feature_names

@callback(
    Output("acoustic-feature-range-slider", "min"),
    Output("acoustic-feature-range-slider", "max"),
    Output("acoustic-feature-range-slider", "value"),
    Output("acoustic-feature-range-slider", "marks"),
    Output("acoustic-feature-range-slider", "step"),
    Output("acoustic-feature-store", "data", allow_duplicate=True),
    State("dataset-select", "value"),
    State("acoustic-feature-store", "data"),
    Input("feature-dropdown", "value"),
    prevent_initial_call=True,
)
def set_acoustic_feature_range_slider(
    dataset_name: str,
    store: Dict[str, Any],
    feature: str,
) -> Tuple[float, float, List[float], Dict[str, str], float, Dict[str, Any]]:
    if not len(store) or store.get("feature") != feature:
        data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name, feature=feature)
        feature_min, feature_max = floor(data["value"].min(), precision=2), ceil(data["value"].max(), precision=2)
        current_min, current_max = feature_min, feature_max
        store = {"feature": feature, "min": feature_min, "max": feature_max, "feature_min": current_min, "feature_max": current_max}
    else:
        feature_min, feature_max = store["min"], store["max"]
        current_min, current_max = store["feature_min"], store["feature_max"]
    marks = {
        f"{floor(value, precision=2)}": f"{floor(value, precision=2)}"
        for value in np.linspace(feature_min, feature_max, 5)
    }
    step = (feature_max - feature_min) / 1e3
    return feature_min, feature_max, [current_min, current_max], marks, step, store

@callback(
    Output("acoustic-feature-store", "data", allow_duplicate=True),
    State("acoustic-feature-store", "data"),
    Input("acoustic-feature-range-slider", "value"),
    prevent_initial_call=True,
)
def set_acoustic_feature_bounds_with_slider(
    store: Dict[str, Any],
    values: List[float],
) -> Dict[str, Any]:
    feature_min, feature_max = values
    store.update({
        "feature_min": feature_min,
        "feature_max": feature_max
    })
    return store

@callback(
    Output("acoustic-feature-range-bounds", "children"),
    Input("acoustic-feature-range-slider", "value"),
)
def update_acoustic_feature_range_bounds(
    values: List[float],
) -> str:
    selected_min, selected_max = values
    return f"{selected_min} - {selected_max}"

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Output("date-range-store", "data", allow_duplicate=True),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def update_date_range(
    dataset_name: str
) -> Tuple[dt.date, dt.date, List[dt.date]]:
    data = dispatch(FETCH_FILES, dataset_name=dataset_name)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    store = {"min": min_date, "max": max_date, "start_date": min_date, "end_date": max_date}
    return min_date, max_date, [min_date, max_date], store

@callback(
    Output("date-range-store", "data", allow_duplicate=True),
    Input("date-picker", "value"),
    State("date-range-store", "data"),
    prevent_initial_call=True,
)
def update_date_store(
    new_date_range: List[str],
    current_date_store: List[str],
) -> Tuple[dt.date, dt.date, List[dt.date]]:
    if len(list(filter(None, new_date_range))) < 2:
        return no_update
    start_date, end_date = new_date_range
    current_date_store.update({
        "start_date": start_date,
        "end_date": end_date,
    })
    return current_date_store

@callback(
    Output("site-level-filter-group", "children"),
    Input("dataset-select", "value"),
)
def init_site_level_filters(
    dataset_name: str,
) -> dmc.Stack:
    params = dict(dataset_name=dataset_name)
    element = SiteLevelHierarchyAccordion(
        tree=dispatch(FETCH_DATASET_SITES_TREE, **params),
        config=dispatch(FETCH_DATASET_CONFIG, **params).get(SITE_HIERARCHY_KEY, {}),
    )
    return element

@callback(
    Output({"type": "checklist-locations-hierarchy", "index": ALL}, "children"),
    Output({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    State("dataset-select", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "children"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_site_level_filters(
    dataset_name: str,
    children: List[List[Dict]],
    values: List[List[str]],
) -> Tuple[List[TreeNodeChip], List[str]]:
    """
    Removes / adds chips based on the depth selection in the tree,

    1. Sub-select children to preserve up to those at the selected node depth
    2. Redraw child nodes of those with the selected parent
    """
    tree = dispatch(FETCH_DATASET_SITES_TREE, dataset_name=dataset_name)
    depth = ctx.triggered_id["index"]
    children = children[:depth]
    flat_values = list(itertools.chain(*values))
    for i in range(len(children) + 1, tree.max_depth):
        nodes = list(sorted(filter(
            lambda node: node.parent.path_name in flat_values,
            bt.levelorder_iter(tree, filter_condition=lambda node: node.depth == i + 1)
        ), key=lambda node: node.path_name))
        chips = [TreeNodeChip(node) for node in nodes]
        values[i - 1] = [node.path_name for node in nodes]
        flat_values = list(itertools.chain(*values))
        children.append(chips)
    return children, values
