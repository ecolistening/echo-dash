import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import callback, Output, Input, State, ALL, ctx
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_DATASETS,
    SET_CURRENT_DATASET,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_FILES,
)

@callback(
    Output("dataset-select", "data"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(_):
    trigger_id = ctx.triggered_id
    action = FETCH_DATASETS
    params = {}
    logger.debug(f"{trigger_id=} {action=} {params=}")
    # FIXME to dataset_id and dataset_name
    datasets = dispatch(action, default=[])
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

@callback(
    Output("feature-dropdown", "value"),
    Output("feature-dropdown", "data"),
    Input("dataset-select", "value"),
)
def fetch_acoustic_feature_names(
    dataset_name: str
) -> Tuple[str, List[str]]:
    trigger_id = ctx.triggered_id
    action = FETCH_ACOUSTIC_FEATURES
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    acoustic_features = dispatch(action, **params)
    feature_names = acoustic_features["feature"].unique()
    return feature_names[0], feature_names

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Input("dataset-select", "value"),
)
def update_date_range(
    dataset_name: str
) -> Tuple[dt.date, dt.date, List[dt.date]]:
    trigger_id = ctx.triggered_id
    action = FETCH_FILES
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    data = dispatch(FETCH_FILES, **params)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    return min_date, max_date, [min_date, max_date]
