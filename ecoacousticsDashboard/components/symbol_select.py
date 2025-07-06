import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger
from typing import Any, Dict, Tuple, List

from api import (
    dispatch,
    FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
)

DEFAULT_SELECT_OPTIONS = dict(
    searchable=True,
    clearable=True,
    persistence=True
)

def SymbolSelect(
    id: str,
    default: str = "",
    data: List[Dict[str, str]] = [],
    style: Dict[str, Any] = dict(width=200),
) -> dmc.Select:
    dataset_select_id = "dataset-select"

    select = dmc.Select(
        id=id,
        label="Symbolise by",
        value=default,
        data=[],
        style=style,
        **DEFAULT_SELECT_OPTIONS,
    )

    @callback(
        Output(select, "data"),
        Output(select, "value"),
        Input(dataset_select_id, "value"),
        State(select, "value"),
    )
    def update(dataset_name: str, symbol_by: str):
        logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {symbol_by=}")
        cat_options = dispatch(
            FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
            dataset_name=dataset_name,
        )
        val_cat_options = [opt["value"] for opt in cat_options]
        if symbol_by not in val_cat_options:
            symbol_by = None
        return cat_options, symbol_by

    return select
