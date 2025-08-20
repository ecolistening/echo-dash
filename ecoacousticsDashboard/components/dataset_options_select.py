import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger
from typing import Any, Dict, Tuple, List

from api import dispatch
from utils import list2tuple

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
    action: str,
    options: List[str] | None = None,
    **kwargs: Any,
) -> dmc.Select:
    select_options = DEFAULT_SELECT_OPTIONS.copy()
    select_options.update(kwargs)

    @callback(
        Output(id, "data"),
        Input("dataset-select", "value"),
    )
    def init_select_options(dataset_name: str) -> List[Dict[str, str]]:
        return dispatch(
            action,
            dataset_name=dataset_name,
            options=list2tuple(options)
        )

    return dmc.Select(id=id, **select_options)
