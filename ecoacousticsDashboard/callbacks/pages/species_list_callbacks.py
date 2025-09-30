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

from api import dispatch, FETCH_SPECIES, FETCH_SPECIES_LIST, SET_SPECIES_LIST

PAGE_SIZE = 120

def register_callbacks():
    @callback(
        Output("species-store", "data"),
        Input("dataset-select", "value"),
    )
    def fetch_current_species_list(
        dataset_name: str,
    ) -> List[str]:
        species_list = dispatch(
            FETCH_SPECIES_LIST,
            dataset_name=dataset_name
        )
        return species_list

    @callback(
        Output("species-list-tickbox", "style"),
        Input("species-store", "data"),
        prevent_initial_call=True,
    )
    def show_species_list_chip(
        species_list: str,
    ) -> Tuple[Dict[str, Any], bool]:
        if len(species_list):
            return {"display": "block"}
        else:
            return {"display": "none"}

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
        Input("species-name-select", "value"),
        Input("species-pagination", "value"),
        Input("species-list-pagination", "value"),
        Input("species-search", "value"),
        Input("species-store", "data"),
        prevent_initial_call=True,
    )
    def render_species_list_checklist(
        dataset_name: str,
        species_column: str,
        letter: str,
        current_page: int,
        search_term: str,
        species_list: List[str],
    ) -> dmc.Box:
        max_str_len = 30
        data = dispatch(FETCH_SPECIES, dataset_name=dataset_name)
        data = data[data["scientific_name"].isin(species_list)]

        if search_term:
            data = data[data[species_column].str.lower().str.contains(search_term.lower())]
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
        Input("species-name-select", "value"),
        Input("species-pagination", "value"),
        Input("species-table-pagination", "value"),
        Input("species-search", "value"),
        Input("species-store", "data"),
        prevent_initial_call=True,
    )
    def render_species_table_checklist(
        dataset_name: str,
        species_column: str,
        letter: str,
        current_page: int,
        search_term: str,
        species_list: List[str],
    ) -> dmc.Box:
        max_str_len = 30
        data = dispatch(FETCH_SPECIES, dataset_name=dataset_name)

        if search_term:
            data = data[data[species_column].str.lower().str.contains(search_term.lower())]
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
        Output({"type": "species-checkbox", "index": ALL}, "checked"),
        Input("species-store", "data"),
        State({"type": "species-checkbox", "index": ALL}, "value"),
    )
    def update_checkboxes_from_store(
        species_list: List[str],
        check_boxes: List[bool],
    ) -> List[str]:
        return [species_name in species_list for species_name in check_boxes]

    @callback(
        Output("species-store", "data", allow_duplicate=True),
        State("species-store", "data"),
        State({"type": "species-checkbox", "index": ALL}, "value"),
        Input({"type": "species-checkbox", "index": ALL}, "checked"),
        prevent_initial_call=True,
    )
    def add_species_to_store(
        species_list: List[str],
        selected_species: List[str],
        check_boxes: List[bool],
    ) -> List[str]:
        page_checked_species = [scientific_name for checked, scientific_name in zip(check_boxes, selected_species) if checked]
        return [*species_list, *page_checked_species]

    @callback(
        Output("species-store", "data", allow_duplicate=True),
        Output("species-list-tickbox", "checked"),
        State("dataset-select", "value"),
        Input("species-list-clear-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_species_store(
        dataset_name: str,
        n_clicks: int,
    ) -> List[str]:
        if n_clicks == 0:
            return no_update, no_update
        dispatch(SET_SPECIES_LIST, dataset_name=dataset_name, species_list=[])
        time.sleep(0.5)
        return [], False

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
        Output("species-store", "data", allow_duplicate=True),
        Output("species-list-save-button", "loading"),
        Input("species-list-save-button", "n_clicks"),
        State("dataset-select", "value"),
        State("species-store", "data"),
        prevent_initial_call=True,
    )
    def save_species_list(
        n_clicks: int,
        dataset_name: str,
        species_list: List[str],
    ) -> List[str]:
        if n_clicks is None or n_clicks == 0:
            return no_update, False
        dispatch(SET_SPECIES_LIST, dataset_name=dataset_name, species_list=species_list)
        time.sleep(0.5)
        return species_list, False
