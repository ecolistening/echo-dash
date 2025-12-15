import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import math
import numpy as np
import pandas as pd
import string
import time

from dash import callback, ctx, no_update, dcc, clientside_callback
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_DATASET_CONFIG,
    SET_DATASET_CONFIG,
    FETCH_DATASET_SITES_TREE,
    FETCH_DATASET_CATEGORY_ORDERS,
    FETCH_DATASET_OPTIONS,
    FETCH_SPECIES,
    SET_SPECIES_LIST,
)

PAGE_SIZE = 120

def register_callbacks():
    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output("settings-sites-save-button", "loading", allow_duplicate=True),
        Input("settings-sites-save-button", "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output("settings-sites-save-button", "loading"),
        State("dataset-select", "value"),
        State({"type": "sitelevel_label", "index": ALL}, "value"),
        Input("settings-sites-save-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def set_dataset_config(
        dataset_name: str,
        site_labels: List[str],
        n_clicks: int,
    ) -> List[str]:
        if not dataset_name or n_clicks is None or n_clicks == 0:
            return no_update
        if site_labels is None or not len(list(filter(None, site_labels))):
            return no_update
        trigger_id = ctx.triggered_id
        action = SET_DATASET_CONFIG
        payload = dict(dataset_name=dataset_name, site_labels=site_labels)
        logger.debug(f"{trigger_id=} {action=} {payload=}")
        time.sleep(1.0) # so the user gets a sense something happened
        return False

    @callback(
        Output("settings-sites-form", "children"),
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
        Output("settings-title", "children"),
        Input("dataset-select", "value"),
    )
    def set_dataset_settings_text(dataset_name: str):
        if not dataset_name:
            return no_update
        return f"{dataset_name} settings"

    @callback(
        Output("species-table", "style"),
        Output("species-list-table", "style"),
        Input("species-list-tickbox", "checked"),
    )
    def switch_tables(checked):
        if checked:
            return {"display": "none"}, {"display": "block"}
        else:
            return {"display": "block"}, {"display": "none"}

    @callback(
        Output("species-pagination", "style"),
        Output("species-pagination", "value"),
        Input("alphabetic-tickbox", "checked"),
    )
    def switch_tables(checked):
        if checked:
            return {"display": "flex"}, "A"
        else:
            return {"display": "none"}, None

    @callback(
        Output("species-list-checklist", "children"),
        Output("species-list-pagination", "total"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("species-name-select", "value"),
        Input("species-pagination", "value"),
        Input("species-list-pagination", "value"),
        Input("species-search", "value"),
        prevent_initial_call=True,
    )
    def render_species_list_checklist(
        dataset_name: str,
        filters: Dict[str, Any],
        species_column: str,
        letter: str,
        current_page: int,
        search_term: str,
    ) -> dmc.Box:
        max_str_len = 30
        data = dispatch(FETCH_SPECIES, dataset_name=dataset_name)
        species_list = filters["species"]
        data = data[data["scientific_name"].isin(species_list)]

        if search_term:
            data = data[(
                data["scientific_name"].str.lower().str.contains(search_term.lower()) |
                data["common_name"].str.lower().str.contains(search_term.lower())
            )]
        elif letter is not None:
            data = data[data[species_column].str.lower().str.startswith(letter.lower(), na=False)]

        data = data.sort_values(by=species_column)
        total = max(1, math.ceil(len(data) / PAGE_SIZE))

        if not len(data):
            return "No species in your species list", total

        start = (current_page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        data = data.iloc[start:end]

        items = []
        for _, row in data.iterrows():
            label = row[species_column]
            if len(label.strip()) == 0:
                label = row["scientific_name"]
            if len(label) > max_str_len:
                label = label[:max_str_len] + "..."
            checkbox = dmc.Checkbox(
                id={"type": "species-checkbox", "index": row["scientific_name"]},
                label=label,
                value=row["scientific_name"],
                checked=row["scientific_name"] in species_list,
                pb="0.25rem",
            )
            items.append(checkbox)

        num_cols = 4
        num_rows = math.ceil(len(items) / num_cols)
        columns = []
        for i in range(num_cols):
            col_items = items[i*num_rows:(i+1)*num_rows]
            columns.append(dmc.GridCol(col_items, span=3))
        return columns, total

    @callback(
        Output("species-table-checklist", "children"),
        Output("species-table-pagination", "total"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("species-name-select", "value"),
        Input("species-pagination", "value"),
        Input("species-table-pagination", "value"),
        Input("species-search", "value"),
        prevent_initial_call=True,
    )
    def render_species_table_checklist(
        dataset_name: str,
        filters: Dict[str, Any],
        species_column: str,
        letter: str,
        current_page: int,
        search_term: str,
    ) -> dmc.Box:
        max_str_len = 30
        data = dispatch(FETCH_SPECIES, dataset_name=dataset_name)
        species_list = filters["species"]

        if search_term:
            data = data[(
                data["scientific_name"].str.lower().str.contains(search_term.lower()) |
                data["common_name"].str.lower().str.contains(search_term.lower())
            )]
        elif letter is not None:
            data = data[data[species_column].str.lower().str.startswith(letter.lower(), na=False)]

        data = data.sort_values(by=species_column)
        total = max(1, math.ceil(len(data) / PAGE_SIZE))
        start = (current_page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        data = data.iloc[start:end]

        items = []
        for _, row in data.iterrows():
            label = row[species_column]
            if len(label.strip()) == 0:
                label = row["scientific_name"]
            if len(label) > max_str_len:
                label = label[:max_str_len] + "..."
            checkbox = dmc.Checkbox(
                id={"type": "species-checkbox", "index": row["scientific_name"]},
                label=label,
                value=row["scientific_name"],
                checked=row["scientific_name"] in species_list,
                pb="0.25rem",
            )
            items.append(checkbox)

        num_cols = 4
        num_rows = math.ceil(len(items) / num_cols)
        columns = []
        for i in range(num_cols):
            col_items = items[i*num_rows:(i+1)*num_rows]
            columns.append(dmc.GridCol(col_items, span=3))
        return columns, total

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        State("filter-store", "data"),
        State({"type": "species-checkbox", "index": ALL}, "value"),
        Input({"type": "species-checkbox", "index": ALL}, "checked"),
        prevent_initial_call=True,
    )
    def add_species_to_store(
        filters: Dict[str, Any],
        selected_species: List[str],
        check_boxes: List[bool],
    ) -> List[str]:
        if selected_species is None or not len(list(filter(None, selected_species))):
            return no_update
        current_species = set(filters["species"])
        for checked, scientific_name in zip(check_boxes, selected_species):
            if checked:
                current_species.add(scientific_name)
            if not checked and scientific_name in current_species:
                current_species.remove(scientific_name)
        species_list = sorted(list(current_species))
        if species_list == current_species:
            return no_update
        filters["species"] = species_list
        return filters

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Output("species-list-tickbox", "checked"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input("species-list-clear-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_species_store(
        dataset_name: str,
        filters: Dict[str, Any],
        n_clicks: int,
    ) -> List[str]:
        if n_clicks is None or n_clicks == 0:
            return no_update, no_update
        species_list = []
        dispatch(SET_SPECIES_LIST, dataset_name=dataset_name, species_list=species_list)
        filters["species"] = species_list
        time.sleep(0.5)
        return filters, False

    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output("species-list-save-button", "loading", allow_duplicate=True),
        Input("species-list-save-button", "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output("species-list-save-button", "loading"),
        Input("species-list-save-button", "n_clicks"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def save_species_list(
        n_clicks: int,
        dataset_name: str,
        filters: List[str],
    ) -> List[str]:
        if n_clicks is None or n_clicks == 0:
            return no_update, False
        species_list = filters["species"]
        dispatch(SET_SPECIES_LIST, dataset_name=dataset_name, species_list=species_list)
        time.sleep(0.5)
        return False
