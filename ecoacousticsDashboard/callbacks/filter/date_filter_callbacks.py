import datetime as dt

from dash import callback, ctx, no_update
from dash import Output, Input, State
from loguru import logger
from typing import Any, Dict, List, Tuple

from utils import floor, ceil
from constants import DateStore

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    State("date-range-store", "data"),
    Input("date-range-current-bounds", "data"),
    prevent_initial_call=True,
)
def set_date_picker_values(
    store: Dict[str, Any],
    bounds: List[str],
) -> Tuple[dt.date, dt.date, List[dt.date]]:
    return store["min"], store["max"], bounds

@callback(
    Output("date-range-current-bounds", "data", allow_duplicate=True),
    Input("date-picker", "value"),
    prevent_initial_call=True,
)
def update_store_bounds_from_picker_values(
    selected_dates: List[str]
) -> List[dt.date]:
    if selected_dates is None or len(list(filter(None, selected_dates))) < 2:
        return no_update
    return selected_dates
