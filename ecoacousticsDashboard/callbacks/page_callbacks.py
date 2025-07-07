import pandas as pd

from dash import html, ctx, dcc, callback, no_update
from dash import Output, Input, State, ALL
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

# @callback(
#     Output("filter-menu", "is_open"),
#     Input("toggle-filter-menu", "n_clicks"),
#     State("filter-menu", "is_open"),
#     prevent_initial_call=True,
# )
# def toggle_filter_menu(n_clicks: int, is_open: bool) -> bool:
#     return not is_open

