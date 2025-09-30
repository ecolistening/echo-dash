import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import math
import numpy as np
import pandas as pd
import string

from dash import callback, ctx, no_update, dcc
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_SPECIES

def register_callbacks():
    @callback(
        Output("species-checklist", "children"),
        Input("dataset-select", "value"),
        Input("species-name-select", "value"),
        Input("species-pagination", "value"),
        Input("species-search", "value"),
        Input("species-store", "data"),
    )
    def render_species_checklist(
        dataset_name: str,
        species_column: str,
        letter: int,
        search_term: str,
        species_list: List[str],
    ) -> dmc.Box:
        max_str_len = 30
        data, all_species_set = dispatch(FETCH_SPECIES, dataset_name=dataset_name)
        if all_species_set == set(species_list):
            return no_update

        if search_term:
            data = data[data[species_column].str.lower().str.contains(search_term.lower())]
        else:
            data = data[data[species_column].str.lower().str.startswith(letter.lower(), na=False)]

        # render all species slows down checking boxes, rethink?
        items = []
        for _, row in data.sort_values(by=species_column).iterrows():
            label = row[species_column]
            if len(label) > max_str_len:
                label = label[:max_str_len] + "..."
            value = row["scientific_name"] + " " + row["common_name"]
            checkbox = dmc.Checkbox(
                id={"type": "species-checkbox", "index": value},
                label=label,
                value=value,
                checked=value in species_list,
                pb="0.25rem",
            )
            items.append(checkbox)

        num_cols = 4
        num_rows = math.ceil(len(items) / num_cols)
        columns = []
        for i in range(num_cols):
            col_items = items[i*num_rows:(i+1)*num_rows]
            columns.append(dmc.GridCol(col_items, span=3))
        return columns

    @callback(
        Output("species-store", "data"),
        State({"type": "species-checkbox", "index": ALL}, "value"),
        Input({"type": "species-checkbox", "index": ALL}, "checked"),
        Input("species-list-clear-button", "n_clicks"),
        State("species-store", "data"),
        prevent_initial_call=True,
    )
    def collect_checked(
        values: List[str],
        check_boxes: List[bool],
        n_clicks: int,
        species_list: List[str],
    ) -> List[str]:
        if n_clicks is not None and n_clicks > 0:
            return []
        return list(
            set([value for checked, value in zip(check_boxes, values) if checked]) |
            set(species_list)
        )
