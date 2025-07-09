import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, ALL, ctx
from loguru import logger
from typing import Any, Dict, List

from api import (
    dispatch,
    FETCH_DATASET_CONFIG,
    SET_DATASET_CONFIG,
    FETCH_DATASET_SITES_TREE,
)
from store import (
    DATASET_CONFIG_STORE,
    SITES_TREE_STORE,
)

@callback(
    Output(DATASET_CONFIG_STORE, "data"),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def get_dataset_config(dataset_name: str) -> Dict[str, Any]:
    trigger_id = ctx.triggered_id
    action = FETCH_DATASET_CONFIG
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    return dispatch(action, dataset_name=dataset_name)

@callback(
    Output(DATASET_CONFIG_STORE, "data", allow_duplicate=True),
    State("dataset-select", "value"),
    State({"type": "sitelevel_label", "index": ALL}, "value"),
    Input("dataset-settings-save-button", "n_clicks"),
    prevent_initial_call=True,
)
def set_dataset_config(
    dataset_name: str,
    site_labels: List[str],
    save_button: int,
) -> List[str]:
    trigger_id = ctx.triggered_id
    action = SET_DATASET_CONFIG
    params = dict(dataset_name=dataset_name, site_labels=site_labels)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    return dispatch(action, **params)

@callback(
    Output(SITES_TREE_STORE, "data"),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def get_dataset_sites_tree(dataset_name: str) -> Dict[str, Any]:
    trigger_id = ctx.triggered_id
    action = FETCH_DATASET_SITES_TREE
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    tree = dispatch(action, **params)
    return bt.tree_to_dict(tree)

@callback(
    Output("dataset-settings-sites-form", "children"),
    Input(DATASET_CONFIG_STORE, "data"),
    Input(SITES_TREE_STORE, "data"),
    prevent_initial_call=True,
)
def set_sites_form(
    config: Dict[str, Any],
    tree_dict: List[str],
) -> List[dmc.TextInput]:
    if config is None or tree_dict is None:
        return []
    tree = bt.dict_to_tree(tree_dict)
    return [
        dmc.TextInput(
            label=f"Level {i}",
            id={"type": "sitelevel_label", "index": i - 1},
            value=config.get("Site Hierarchy").get(f"sitelevel_{i}", ""),
        )
        for i in range(1, tree.max_depth)
    ]

@callback(
    Output("dataset-settings-dataset-name", "children"),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def set_dataset_settings_text(dataset_name: str):
    return f"Settings for the {dataset_name} dataset"

@callback(
    Output("settings-drawer", "opened"),
    Input("dataset-settings-button", "n_clicks"),
    Input("dataset-settings-cancel-button", "n_clicks"),
    Input(DATASET_CONFIG_STORE, "data"),
    prevent_initial_call=True,
)
def toggle_settings_drawer(*args: Any):
    if ctx.triggered_id == "dataset-settings-button":
        return True
    elif ctx.triggered_id == "dataset-settings-cancel-button":
        return False
    return False
