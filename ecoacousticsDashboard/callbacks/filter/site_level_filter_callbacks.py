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

from api import dispatch, FETCH_DATASET_SITES_TREE, FETCH_DATASET_CONFIG
from components.site_level_filter import SiteLevelHierarchyAccordion, TreeNodeChip

SITE_HIERARCHY_KEY = "Site Hierarchy"

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
