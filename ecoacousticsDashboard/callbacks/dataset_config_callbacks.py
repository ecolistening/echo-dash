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
        if not dataset_name:
            return no_update
        trigger_id = ctx.triggered_id
        action = FETCH_DATASET_CONFIG
        payload = dict(dataset_name=dataset_name)
        logger.debug(f"{trigger_id=} {action=} {payload=}")
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
        n_clicks: int,
    ) -> List[str]:
        if not dataset_name or n_clicks is None or n_clicks == 0:
            return no_update
        trigger_id = ctx.triggered_id
        action = SET_DATASET_CONFIG
        payload = dict(dataset_name=dataset_name, site_labels=site_labels)
        logger.debug(f"{trigger_id=} {action=} {payload=}")
        return dispatch(action, **payload)

    @callback(
        Output("dataset-settings-sites-form", "children"),
        Input("dataset-select", "value"),
    )
    def set_sites_form(
        dataset_name: str
    ) -> List[dmc.TextInput]:
        if not dataset_name:
            return no_update
        payload = dict(dataset_name=dataset_name)

        action = FETCH_DATASET_CONFIG
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        config = dispatch(action, **payload)

        action = FETCH_DATASET_SITES_TREE
        logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
        tree = dispatch(action, **payload)

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
        if not dataset_name:
            return no_update
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
