import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, ctx, no_update, html
from dash import Output, Input, State

from utils.content import get_content

def register_callbacks():
    @callback(
        Output("feature-descriptor-content", "children"),
        Input("feature-select", "value"),
    )
    def show_feature_description(
        current_feature: str,
    ) -> html.Div:
        if not current_feature:
            return no_update
        return get_content(f"feature/{current_feature}")
