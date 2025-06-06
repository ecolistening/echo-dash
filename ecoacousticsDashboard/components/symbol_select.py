import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger
from typing import Any, Dict

from utils.data import dataset_loader, DatasetDecorator

DEFAULT_SELECT_OPTIONS = dict(
    searchable=True,
    clearable=True,
    persistence=True
)

def SymbolSelect(
    id: str,
    default: str = None,
    style: Dict[str, Any] = dict(width=200),
) -> dmc.Select:
    dataset_select_id = "dataset-select"

    select = dmc.Select(
        id=id,
        label="Symbolise by",
        value=default,
        style=style,
        **DEFAULT_SELECT_OPTIONS,
    )

    @callback(
        Output(select, "data"),
        Input(dataset_select_id, "value"),
        State(select, "value"),
    )
    def update(dataset_name: str, symbol_by: str):
        logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {symbol_by=}")
        decorator = DatasetDecorator(dataset_loader.get_dataset(dataset_name))
        cat_options = decorator.categorical_drop_down_select_options()
        val_cat_options = [opt["value"] for opt in cat_options]
        if symbol_by not in val_cat_options:
            symbol_by = None
        return cat_options

    return select
