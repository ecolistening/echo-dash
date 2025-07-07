import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger
from typing import Any, Dict, Tuple, List

from api import (
    dispatch,
    FETCH_DATASET_DROPDOWN_OPTIONS,
)

DEFAULT_SELECT_OPTIONS = dict(
    nothingFoundMessage="Options not found...",
    searchable=True,
    clearable=True,
    allowDeselect=True,
    persistence=True,
    style=dict(width=200),
    data=[],
    value=None,
)

def DatasetOptionsSelect(
    id: str,
    categorical: bool = False,
    **kwargs: Any,
) -> dmc.Select:
    select_options = DEFAULT_SELECT_OPTIONS.copy()
    select_options.update(kwargs)

    @callback(
        Output(id, "data"),
        Input("dataset-select", "value"),
    )
    def init_select_options(dataset_name: str) -> List[Dict[str, str]]:
        triggered_id = ctx.triggered_id
        action = FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS if categorical else FETCH_DATASET_DROPDOWN_OPTIONS
        params = dict(dataset_name=dataset_name)
        return dispatch(action, **params)

    return dmc.Select(id=id, **select_options)
