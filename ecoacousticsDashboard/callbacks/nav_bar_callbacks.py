import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, ALL, ctx, no_update
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_DATASETS,
)

@callback(
    Output("appshell", "navbar"),
    Input("burger", "opened"),
    State("appshell", "navbar"),
)
def navbar_is_open(
    opened: bool,
    navbar: Dict[str, str],
) -> Dict[str, str]:
    navbar["collapsed"] = {"desktop": not opened, "mobile": not opened }
    return navbar

@callback(
    Output("dataset-select", "data"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(_) -> List[Dict[str, str]]:
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

