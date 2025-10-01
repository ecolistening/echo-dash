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

from api import dispatch, FETCH_SPECIES, SET_SPECIES_LIST

PAGE_SIZE = 120

def register_callbacks():
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
        logger.info(f"Rendering list {species_list=}")

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
        logger.info(f"Rendering table {species_list=}")

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
        page_checked_species = [scientific_name for checked, scientific_name in zip(check_boxes, selected_species) if checked]
        current_species = filters["species"]
        species_list = list(set(current_species) | set(page_checked_species))
        species_list = list(sorted(species_list))
        logger.info(f"Checking {species_list=} {current_species=} {current_species == species_list}")
        if species_list == current_species:
            return no_update
        filters["species"] = species_list
        logger.info(f"Added to filters {species_list=}")
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
        logger.info(f"Species reset")
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
        logger.info(f"Saving {species_list=}")
        dispatch(SET_SPECIES_LIST, dataset_name=dataset_name, species_list=species_list)
        time.sleep(0.5)
        return False
