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
    FETCH_DATASET_CATEGORY_ORDERS,
    FETCH_DATASET_OPTIONS,
)

def register_callbacks():
    @callback(
        Output("dataset-config", "data"),
        Input("dataset-select", "value"),
    )
    def get_dataset_config(dataset_name: str) -> Dict[str, Any]:
        trigger_id = ctx.triggered_id
        action = FETCH_DATASET_CONFIG
        params = dict(dataset_name=dataset_name)
        logger.debug(f"{trigger_id=} {action=} {params=}")
        return dispatch(action, dataset_name=dataset_name)

    @callback(
        Output("dataset-config", "data", allow_duplicate=True),
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
        Output("dataset-settings-sites-form", "children"),
        Input("dataset-select", "value"),
    )
    def set_sites_form(
        dataset_name: str
    ) -> List[dmc.TextInput]:
        params = dict(dataset_name=dataset_name)
        config = dispatch(FETCH_DATASET_CONFIG, **params)
        tree = dispatch(FETCH_DATASET_SITES_TREE, **params)
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
    )
    def set_dataset_settings_text(dataset_name: str):
        return f"Settings for the {dataset_name} dataset"

    @callback(
        Output("settings-drawer", "opened"),
        Input("dataset-settings-button", "n_clicks"),
        Input("dataset-settings-cancel-button", "n_clicks"),
        Input("dataset-config", "data"),
    )
    def toggle_settings_drawer(*args: Any):
        if ctx.triggered_id == "dataset-settings-button":
            return True
        elif ctx.triggered_id == "dataset-settings-cancel-button":
            return False
        return False

    @callback(
        Output("dataset-category-orders", "data"),
        Input("dataset-select", "value"),
    )
    def load_categories(
        dataset_name: str,
    ) -> Dict[str, List[str]]:
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        return category_orders

    @callback(
        Output("dataset-options", "data"),
        Input("dataset-select", "value"),
    )
    def load_options(
        dataset_name: str,
    ) -> Dict[str, List[str]]:
        return dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
