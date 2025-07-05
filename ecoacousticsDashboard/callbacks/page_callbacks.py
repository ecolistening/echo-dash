from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL

@callback(
    Output("page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open
