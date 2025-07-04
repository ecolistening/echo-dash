import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger
from typing import Any, Dict, Tuple

from api import (
    dispatch,
    FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
    FETCH_DATASET_DROPDOWN_OPTIONS,
)

DEFAULT_SELECT_OPTIONS = dict(
    searchable=True,
    clearable=True,
    persistence=True
)

def ColourSelect(
    id: str,
    default=None,
    style: Dict[str, Any] = dict(width=200),
    categorical: bool = False,
) -> dmc.Select:
    dataset_select_id = 'dataset-select'

    select = dmc.Select(
        id=id,
        label="Colour by",
        value=default,
        style=style,
        **DEFAULT_SELECT_OPTIONS
    )

    @callback(
        Output(select, "data"),
        Output(select, "value"),
        Input(dataset_select_id, "value"),
        State(select, "value"),
    )
    def update(dataset_name: str, colour_by: str) -> Tuple[str, ...]:
        logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {colour_by=}")

        cat_options = dispatch(
            FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
            dataset_name=dataset_name,
        )
        val_cat_options = [opt['value'] for opt in cat_options]

        if categorical:
            options = cat_options
            val_options = val_cat_options
        else:
            options = dispatch(
                FETCH_DATASET_DROPDOWN_OPTIONS,
                dataset_name=dataset_name,
            )
            val_options = [opt['value'] for opt in options]

        if colour_by not in val_options:
            colour_by = None

        return options, colour_by

    return select
