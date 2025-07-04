import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, html
from loguru import logger
from typing import Any, List, Dict

from store.dataset import DATASET_STORE, DATASETS_STORE

dataset_select_id = "dataset-select"

def DatasetSelect():
    return dmc.Select(
        id=dataset_select_id,
        label="Dataset",
        description="Select a dataset to explore",
        searchable=True,
        nothingFound="No options found",
        clearable=False,
        value=None,
        persistence=True,
    )
