import datetime as dt
import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import html, dcc, callback, ctx
from dash import Output, Input, State
from loguru import logger
from typing import List, Tuple

from api import dispatch, FETCH_FILES

def DatePicker(
    min_date: dt.date = dt.date(1970, 1, 1),
    max_date: dt.date = dt.date.today(),
) -> dmc.DateRangePicker:
    date_picker_id = "date-picker"

    @callback(
        Output(date_picker_id, "minDate"),
        Output(date_picker_id, "maxDate"),
        Output(date_picker_id, "value"),
        Input("dataset-select", "value"),
    )
    def update_date_range(
        dataset_name: str
    ) -> Tuple[dt.date, dt.date, List[dt.date]]:
        trigger_id = ctx.triggered_id
        action = FETCH_FILES
        params = dict(dataset_name=dataset_name)
        logger.debug(f"{trigger_id} {action=} {params=}")
        data = dispatch(FETCH_FILES, **params)
        min_date = data.timestamp.dt.date.min()
        max_date = data.timestamp.dt.date.max()
        return min_date, max_date, [min_date, max_date]

    return dmc.DateRangePicker(
        id=date_picker_id,
        label="Date Range",
        description="To include in plots",
        minDate=min_date,
        maxDate=max_date,
        value=[min_date, max_date],
        clearable=True,
        persistence=True,
    )
