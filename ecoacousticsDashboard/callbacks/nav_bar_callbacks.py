import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import callback, ctx, no_update
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_DATASETS

def register_callbacks():
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
        Output("dataset-select", "value"),
        Output("dataset-select", "data"),
        State("dataset-select", "value"),
        Input("load-datasets", "n_intervals"),
    )
    def fetch_datasets(current_dataset, _) -> List[Dict[str, str]]:
        action = FETCH_DATASETS
        logger.debug(f"{ctx.triggered_id=} {action=}")
        datasets = dispatch(action, default=[])
        dataset_options = [
            dict(label=dataset, value=dataset)
            for dataset in datasets
        ]
        if current_dataset is None or not len(current_dataset):
            current_dataset = dataset_options[0]["value"]
        return current_dataset, dataset_options
