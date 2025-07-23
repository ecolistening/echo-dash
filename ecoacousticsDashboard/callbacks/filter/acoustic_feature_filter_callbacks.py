import numpy as np

from dash import callback, ctx, no_update
from dash import Output, Input, State
from loguru import logger
from typing import Any, Dict, List, Tuple

from utils import floor, ceil
from constants import AcousticFeatureStore

@callback(
    Output("feature-dropdown", "value"),
    Output("feature-dropdown", "data"),
    State("acoustic-feature-store", "data"),
    Input("acoustic-feature-current-bounds", "data"),
    prevent_initial_call=True,
)
def set_dropdown_from_store(
    store: AcousticFeatureStore,
    state: Dict[str, Any],
) -> Tuple[str, List[str]]:
    return state["feature"], list(store.keys())

@callback(
    Output("acoustic-feature-current-bounds", "data", allow_duplicate=True),
    State("acoustic-feature-store", "data"),
    State("acoustic-feature-current-bounds", "data"),
    Input("feature-dropdown", "value"),
    prevent_initial_call=True,
)
def set_state_from_dropdown(
    store: AcousticFeatureStore,
    state: Dict[str, Any],
    feature: str,
) -> Tuple[str, List[str]]:
    if feature is None or (feature is not None and feature == state["feature"]):
        return state
    return {
        "feature": feature,
        "start_value": store[feature]["min"],
        "end_value": store[feature]["max"]
    }

@callback(
    Output("acoustic-feature-range-slider", "min"),
    Output("acoustic-feature-range-slider", "max"),
    Output("acoustic-feature-range-slider", "value"),
    Output("acoustic-feature-range-slider", "marks"),
    Output("acoustic-feature-range-slider", "step"),
    State("acoustic-feature-store", "data"),
    Input("acoustic-feature-current-bounds", "data"),
    prevent_initial_call=True,
)
def set_range_slider_from_store(
    store: AcousticFeatureStore,
    state: Dict[str, Any],
) -> Tuple[Any]:
    feature = state["feature"]
    marks = {f"{floor(value, precision=2)}": f"{floor(value, precision=2)}" for value in np.linspace(store[feature]["min"], store[feature]["max"], 5)}
    step = (store[feature]["max"] - store[feature]["min"]) / 1e3
    return store[feature]["min"], store[feature]["max"], [state["start_value"], state["end_value"]], marks, step

@callback(
    Output("acoustic-feature-current-bounds", "data", allow_duplicate=True),
    State("acoustic-feature-current-bounds", "data"),
    Input("acoustic-feature-range-slider", "value"),
    prevent_initial_call=True,
)
def update_state_from_slider(
    state: Dict[str, Any],
    values: List[float],
) -> AcousticFeatureStore:
    if values is None: return no_update
    start_value, end_value = values
    return {
        "feature": state["feature"],
        "start_value": start_value,
        "end_value": end_value,
    }

@callback(
    Output("acoustic-feature-range-bounds", "children"),
    Input("acoustic-feature-range-slider", "value"),
    prevent_initial_call=True,
)
def update_description_text_from_slider(
    values: List[float],
) -> str:
    selected_min, selected_max = values
    return f"{selected_min} - {selected_max}"
