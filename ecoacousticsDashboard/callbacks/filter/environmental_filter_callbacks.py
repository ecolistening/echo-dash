from dash import callback, ctx, no_update
from dash import Output, Input, State
from dash import MATCH, ALL
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from components.environmental_filter import EnvironmentalFilterSliderAccordion
from utils import list2tuple

@callback(
    Output("weather-variable-filter-groups", "children"),
    Input("dataset-select", "value"),
)
def populate_environmental_filter(dataset_name: str):
    opt_groups = dispatch(
        FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
        dataset_name=dataset_name,
        options=("Temperature", "Precipitation", "Wind"),
        default=[],
    )
    return [
        EnvironmentalFilterSliderAccordion(**opt_group)
        for opt_group in opt_groups
    ]
