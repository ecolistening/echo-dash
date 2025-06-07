import requests

from dash import callback, Output, Input
from typing import Any, Dict, List

from components.dataset_select import dataset_select_id
from components.nav_bar import load_datasets_id
from store import DATASET_STORE, DATASETS_STORE

DATASET_STORE = "dataset-name"
DATASETS_STORE = "datasets"

@callback(
    Output(DATASETS_STORE, "data"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(_):
    try:
        response = requests.get("http://localhost:8000/api/v1/datasets")
        return response.json()
    except:
        return []

@callback(
    Output(DATASET_STORE, "data"),
    Input(DATASETS_STORE, "data"),
)
def set_default_dataset(datasets: list[str]):
    if not datasets:
        return None
    try:
        response = requests.post("http://localhost:8000/api/v1/dataset", json=dict(dataset_name=datasets[0]))
        return response.json()["dataset_name"]
    except:
        return None

@callback(
    Output(DATASET_STORE, "data", allow_duplicate=True),
    Input(dataset_select_id, "value"),
    prevent_initial_call=True,
)
def change_dataset(dataset_name: str) -> str:
    try:
        response = requests.post("http://localhost:8000/api/v1/dataset", json=dict(dataset_name=dataset_name))
        return response.json()["dataset_name"]
    except:
        return dataset_name

@callback(
    Output(dataset_select_id, "data"),
    Input(DATASETS_STORE, "data"),
    prevent_initial_call=True,
)
def populate_datasets_selector(datasets: List[str] | None) -> List[Dict[str, Any]]:
    if not datasets:
        return []
    else:
        return [
            dict(label=dataset, value=dataset)
            for dataset in datasets
        ]

@callback(
    Output(dataset_select_id, "value"),
    Input(DATASET_STORE, "data"),
    prevent_initial_call=True,
)
def set_dataset_selector_default(dataset_name: str) -> List[Dict[str, Any]]:
    return dataset_name
