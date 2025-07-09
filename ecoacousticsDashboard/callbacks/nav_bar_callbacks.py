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

from api import (
    dispatch,
    FETCH_DATASETS,
    SET_CURRENT_DATASET,
    FETCH_DATASET_SITES_TREE,
    FETCH_DATASET_CONFIG,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_FILES,
)

SITE_HIERARCHY_KEY = "Site Hierarchy"

def ceil(a, precision=0):
    return np.round(a + 0.5 * 10**(-precision), precision)

def floor(a, precision=0):
    return np.round(a - 0.5 * 10**(-precision), precision)

@callback(
    Output("appshell", "navbar"),
    Input("burger", "opened"),
    State("appshell", "navbar"),
)
def navbar_is_open(opened, navbar):
    navbar["collapsed"] = {"desktop": not opened, "mobile": not opened }
    return navbar

@callback(
    Output("dataset-select", "data"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(_):
    # FIXME to dataset_id and dataset_name
    datasets = dispatch(FETCH_DATASETS, default=[])
    return [
        dict(label=dataset, value=dataset)
        for dataset in datasets
    ]

@callback(
    Output("dataset-select", "value"),
    Input("dataset-select", "data"),
    prevent_initial_call=True
)
def set_default_dataset(dataset_options: List[str]):
    return dataset_options[0]["value"]

@callback(
    Output("feature-dropdown", "value"),
    Output("feature-dropdown", "data"),
    Output("acoustic-feature-range-slider", "min"),
    Output("acoustic-feature-range-slider", "max"),
    Input("dataset-select", "value"),
)
def set_acoustic_feature(
    dataset_name: str
) -> Tuple[str, List[str], float, float]:
    acoustic_features = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
    feature_names = acoustic_features["feature"].unique()
    selected_feature = feature_names[0]
    feature_min = floor(acoustic_features.loc[acoustic_features["feature"] == selected_feature, "value"].min(), precision=2)
    feature_max = ceil(acoustic_features.loc[acoustic_features["feature"] == selected_feature, "value"].max(), precision=2)
    return (
        selected_feature,
        feature_names,
        feature_min,
        feature_max,
    )

@callback(
    Output("acoustic-feature-range-slider", "value"),
    Output("acoustic-feature-range-slider", "marks"),
    Output("acoustic-feature-range-slider", "step"),
    Input("acoustic-feature-range-slider", "min"),
    Input("acoustic-feature-range-slider", "max"),
)
def update_acoustic_feature_range_slider(
    feature_min: float,
    feature_max: float,
) -> Tuple[Any, ...]:
    return (
        [feature_min, feature_max],
        slider_marks := {
            f"{floor(value, precision=2)}": f"{floor(value, precision=2)}"
            for value in np.linspace(feature_min, feature_max, 5)
        },
        step := (feature_max - feature_min) / 1e3,
    )

@callback(
    Output("acoustic-feature-range-bounds", "children"),
    Input("acoustic-feature-range-slider", "value"),
)
def update_acoustic_feature_range_bounds(
    value: List[float],
) -> str:
    selected_min, selected_max = value
    return f"{selected_min} - {selected_max}"

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Input("dataset-select", "value"),
)
def update_date_range(
    dataset_name: str
) -> Tuple[dt.date, dt.date, List[dt.date]]:
    data = dispatch(FETCH_FILES, dataset_name=dataset_name)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    return min_date, max_date, [min_date, max_date]

@callback(
    Output("site-level-filter-group", "children"),
    Input("dataset-select", "value"),
)
def init_site_level_filters(
    dataset_name: str,
) -> dmc.Stack:
    params = dict(dataset_name=dataset_name)
    return SiteLevelHierarchyAccordion(
        tree=dispatch(FETCH_DATASET_SITES_TREE, **params),
        config=dispatch(FETCH_DATASET_CONFIG, **params).get(SITE_HIERARCHY_KEY, {}),
    )

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
