import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, ALL, MATCH, ctx
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS
)

@callback(
    Output({"type": "colour-select", "index": MATCH}, "data"),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def update_colour_data(dataset_name):
    options = dispatch(FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS, dataset_name=dataset_name)
    return options or []

@callback(
    Output({"type": "colour-select", "index": MATCH}, "value"),
    Input("dataset-select", "value"),
    State({"type": "colour-select", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_colour_value(dataset_name, colour):
    options = dispatch(FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS, dataset_name=dataset_name)
    valid_values = [opt["value"] for opt in (options or [])]
    return colour if colour in valid_values else None

# @callback(
#     Output({"type": "colour-select", "index": MATCH}, "data"),
#     Output({"type": "colour-select", "index": MATCH}, "value"),
#     Input("dataset-select", "value"),
#     Input({"type": "colour-select", "index": MATCH}, "value"),
#     prevent_initial_call=True,
# )
# def update_colour_by(
#     dataset_name: str,
#     colour: str,
# ):
#     logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {colour=}")
#     cat_options = dispatch(
#         FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
#         dataset_name=dataset_name,
#     )
#     val_cat_options = [opt["value"] for opt in cat_options]
#     if colour not in val_cat_options:
#         colour = None
#     logger.debug(f"COLOUR OPTS: {cat_options}")
#     return cat_options, colour

# @callback(
#     Output({"type": "symbol-select", "index": MATCH}, "data"),
#     Output({"type": "symbol-select", "index": MATCH}, "value"),
#     Input("dataset-select", "value"),
#     Input({"type": "symbol-select", "index": MATCH}, "value"),
#     prevent_initial_call=True,
# )
# def update_symbol_by(
#     dataset_name: str,
#     symbol: str,
# ):
#     logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {symbol=}")
#     cat_options = dispatch(
#         FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
#         dataset_name=dataset_name,
#     )
#     val_cat_options = [opt["value"] for opt in cat_options]
#     if symbol not in val_cat_options:
#         symbol = None
#     logger.debug(f"SYM OPTS: {cat_options}")
#     return cat_options, symbol

# @callback(
#     Output({"type": "facet-row-select", "index": MATCH}, "data"),
#     Output({"type": "facet-row-select", "index": MATCH}, "value"),
#     Input("dataset-select", "value"),
#     Input({"type": "facet-row-select", "index": MATCH}, "value"),
#     prevent_initial_call=True,
# )
# def update_facet_row_by(
#     dataset_name: str,
#     facet_row: str,
# ):
#     logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {facet_row=}")
#     cat_options = dispatch(
#         FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
#         dataset_name=dataset_name,
#     )
#     val_cat_options = [opt["value"] for opt in cat_options]
#     if facet_row not in val_cat_options:
#         facet_row = None
#     logger.debug(f"ROW OPTS: {cat_options}")
#     return cat_options, facet_row

# @callback(
#     Output({"type": "facet-col-select", "index": MATCH}, "data"),
#     Output({"type": "facet-col-select", "index": MATCH}, "value"),
#     Input("dataset-select", "value"),
#     Input({"type": "facet-col-select", "index": MATCH}, "value"),
#     prevent_initial_call=True,
# )
# def update_facet_col_by(
#     dataset_name: str,
#     facet_col: str
# ):
#     logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {facet_col=}")
#     cat_options = dispatch(
#         FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS,
#         dataset_name=dataset_name,
#     )
#     val_cat_options = [opt["value"] for opt in cat_options]
#     if facet_col not in val_cat_options:
#         facet_col = None
#     logger.debug(f"COL OPTS: {cat_options}")
#     return cat_options, facet_col
