import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger
from typing import Any, Dict, List

from api import (
    dispatch,
    FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
)

DEFAULT_SELECT_OPTIONS = dict(
    searchable=True,
    clearable=True,
    persistence=True
)

def RowFacetSelect(
    id: str,
    default: str = None,
    style: Dict[str, Any] = dict(width=200),
    ignore_options: List[str] = [],
) -> dmc.Select:
    dataset_select_id = "dataset-select"

    select = dmc.Select(
        id=id,
        label="Facet Rows by",
        value="location",
        style=style,
        **DEFAULT_SELECT_OPTIONS,
    )

    @callback(
        Output(select, "data"),
        Output(select, "value"),
        Input(dataset_select_id, "value"),
        State(select, "value"),
    )
    def update(dataset_name: str, row_facet: str):
        logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {row_facet=}")
        options = dispatch(
            FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
            dataset_name=dataset_name,
        )
        cat_options = [opt for opt in options if opt["value"] not in ignore_options]
        val_cat_options = [opt["value"] for opt in cat_options]
        if row_facet not in val_cat_options:
            row_facet = None
        return cat_options, row_facet

    return select

def ColumnFacetSelect(
    id: str,
    default: str = None,
    style: Dict[str, Any] = dict(width=200),
    ignore_options: List[str] = [],
) -> dmc.Select:
    dataset_select_id = "dataset-select"

    select = dmc.Select(
        id=id,
        label="Facet Columns by",
        value="location",
        style=style,
        **DEFAULT_SELECT_OPTIONS,
    )

    @callback(
        Output(select, "data"),
        Output(select, "value"),
        Input(dataset_select_id, "value"),
        State(select, "value"),
    )
    def update(dataset_name: str, col_facet: str):
        logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {col_facet=}")
        options = dispatch(
            FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
            dataset_name=dataset_name,
        )
        cat_options = [opt for opt in options if opt["value"] not in ignore_options]
        val_cat_options = [opt["value"] for opt in cat_options]
        if col_facet not in val_cat_options:
            col_facet = None
        return cat_options, col_facet

    return select
