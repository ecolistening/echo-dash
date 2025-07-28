from dash import callback, ctx, no_update
from dash import Output, Input, State
from dash import MATCH, ALL
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_DATASET_WEATHER_OPTIONS
from components.environmental_filter import EnvironmentalFilterSliderAccordion

@callback(
    Output("weather-variable-filter-groups", "children"),
    Input("dataset-select", "value"),
)
def populate_environmental_filter(dataset_name: str):
    opt_groups = dispatch(FETCH_DATASET_WEATHER_OPTIONS, dataset_name=dataset_name)
    return [EnvironmentalFilterSliderAccordion(**opt_group) for opt_group in opt_groups]
