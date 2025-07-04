import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import html, dcc, callback, ctx
from dash import Output, Input, State
from loguru import logger
from typing import List, Tuple

from api import (
    dispatch,
    FETCH_ACOUSTIC_FEATURES,
)

def FeatureSelect():
    feature_select_id = "feature-dropdown"

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
        logger.debug(f"{trigger_id} {action=} {params=}")
        acoustic_features = dispatch(action, **params)
        feature_names = acoustic_features["feature"].unique()
        return feature_names[0], feature_names

    return dmc.Select(
        label="Acoustic Descriptor",
        description="Select an acoustic desscriptor",
        id=feature_select_id,
        data=[],
        value="",
        searchable=True,
        dropdownPosition="bottom",
        clearable=False,
        persistence=True,
    )
