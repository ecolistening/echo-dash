import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, ALL, ctx
from loguru import logger
from typing import Any, Dict, List

from api import (
    dispatch,
    FETCH_DATASETS,
    SET_CURRENT_DATASET,
    FETCH_DATASET_CONFIG,
    SET_DATASET_CONFIG,
    FETCH_DATASET_SITES_TREE,
)
from store import (
    DATASET_STORE,
    DATASETS_STORE,
    DATASET_CONFIG_STORE,
    SITES_TREE_STORE,
)
from components.nav_bar import (
    load_datasets_id,
    settings_drawer_id,
    dataset_settings_button_id,
    dataset_settings_save_button_id,
    dataset_settings_cancel_button_id,
    dataset_settings_sites_form_id,
    dataset_settings_dataset_name_id,
)
from components.dataset_select import (
    dataset_select_id,
)

@callback(
    Output(DATASETS_STORE, "data"),
    Input(load_datasets_id, "n_intervals"),
)
def fetch_datasets(_):
    logger.debug("Fetching datasets")
    return dispatch(
        FETCH_DATASETS,
        default=[]
    )

@callback(
    Output(DATASET_STORE, "data"),
    Input(DATASETS_STORE, "data"),
)
def set_default_dataset(datasets: list[str]):
    if not datasets: return None
    dataset_name = dispatch(
        SET_CURRENT_DATASET,
        payload=dict(dataset_name=datasets[0]),
        default={},
    ).get("dataset_name", None)
    logger.debug(f"Current dataset set to default: {dataset_name}")
    return dataset_name

@callback(
    Output(DATASET_STORE, "data", allow_duplicate=True),
    Input(dataset_select_id, "value"),
    prevent_initial_call=True,
)
def set_current_dataset(dataset_name: str) -> str:
    dataset_name = dispatch(
        SET_CURRENT_DATASET,
        payload=dict(dataset_name=dataset_name),
        default={},
    ).get("dataset_name", None)
    logger.debug(f"Current dataset set to: {dataset_name}")
    return dataset_name

@callback(
    Output(dataset_select_id, "data"),
    Input(DATASETS_STORE, "data"),
    prevent_initial_call=True,
)
def populate_datasets_selector(datasets: List[str] = []) -> List[Dict[str, Any]]:
    return [
        dict(label=dataset, value=dataset)
        for dataset in datasets
    ]

@callback(
    Output(dataset_select_id, "value"),
    Input(DATASET_STORE, "data"),
    prevent_initial_call=True,
)
def set_dataset_selector_default(dataset_name: str) -> str:
    return dataset_name

# ------ Config GET/SET Methods ----- #

@callback(
    Output(DATASET_CONFIG_STORE, "data"),
    Input(DATASET_STORE, "data"),
    prevent_initial_call=True,
)
def get_dataset_config(dataset_name: str) -> Dict[str, Any]:
    return dispatch(
        FETCH_DATASET_CONFIG,
        payload=dict(dataset_name=dataset_name),
        default={},
    )

@callback(
    Output(DATASET_CONFIG_STORE, "data", allow_duplicate=True),
    Input(dataset_settings_save_button_id, "n_clicks"),
    State({"type": "sitelevel_label", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def set_dataset_config(save_button, site_labels):
    return dispatch(
        SET_DATASET_CONFIG,
        payload=dict(site_labels=site_labels),
        default={},
    )

@callback(
    Output(SITES_TREE_STORE, "data"),
    Input(DATASET_STORE, "data"),
    prevent_initial_call=True,
)
def get_dataset_sites_tree(dataset_name: str) -> Dict[str, Any]:
    return dispatch(
        FETCH_DATASET_SITES_TREE,
        payload=dict(dataset_name=dataset_name),
        default=[],
    )

@callback(
    Output(dataset_settings_sites_form_id, "children"),
    Input(DATASET_CONFIG_STORE, "data"),
    Input(SITES_TREE_STORE, "data"),
    prevent_initial_call=True,
)
def set_sites_form(config: Dict[str, Any], tree_dict: Dict[str, Any]) -> List[dmc.TextInput]:
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
    Output(dataset_settings_dataset_name_id, "children"),
    Input(DATASET_STORE, "data"),
)
def set_dataset_settings_text(dataset_name: str):
    return f"Settings for the {dataset_name} dataset"

@callback(
    Output(settings_drawer_id, "opened"),
    Input(dataset_settings_button_id, "n_clicks"),
    Input(dataset_settings_cancel_button_id, "n_clicks"),
    Input(DATASET_CONFIG_STORE, "data"),
    prevent_initial_call=True,
)
def toggle_settings_drawer(*args: Any):
    if ctx.triggered_id == dataset_settings_button_id:
        return True
    elif ctx.triggered_id == dataset_settings_cancel_button_id:
        return False
    return False
