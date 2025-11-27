import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update, clientside_callback
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_ACOUSTIC_FEATURES
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, capitalise_each, send_download, safe_category_orders
from utils.sketch import default_layout

PLOT_HEIGHT = 400

def fetch_data(dataset_name, filters):
    action = FETCH_ACOUSTIC_FEATURES
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("index-averages-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("index-averages-time-aggregation", "value"),
        Input("index-averages-colour-select", "value"),
        Input("index-averages-year-wrap-checkbox", "checked"),
        # Input(outliers_tickbox, "checked"),
        # Input(colours_tickbox, "checked"),
        # Input(separate_plots_tickbox, "checked"),
        Input("plotly-theme", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        time_agg: str,
        color: str,
        annual_wrap: bool,
        # outliers,
        # colour_locations,
        # separate_plots,
        template: str,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters)

        if annual_wrap:
            data["_time"] = data["timestamp"].apply(lambda dt: dt.replace(year=1972))
            x_tick_format = "%b"
        else:
            data["_time"] = data["timestamp"]
            x_tick_format = "%b %Y"

        data = (
            data.sort_values("_time")
            .groupby(list(filter(None, [color, "feature", "dddn", pd.Grouper(key="_time", freq=time_agg)])))
            .agg(value_mean=("value", "mean"), value_std=("value", "std"))
            .reset_index()
        )

        fig = px.line(
            data_frame=data,
            x="_time",
            y="value_mean",
            error_y="value_std",
            color=color,
            facet_row="dddn",
            markers=True,
            labels={
                "_time": "Time",
                "value_mean": "Value",
                color: options.get(color, {}).get("label", color),
            },
            category_orders=safe_category_orders(data, category_orders),
        )

        fig.update_traces(marker=dict(size=4))
        fig.update_xaxes(tickformat=x_tick_format)
        fig.update_layout(default_layout(fig))
        fig.update_layout(title_text=f"{capitalise_each(filters['current_feature'])} Seasonal Averages")
        fig.update_layout(template=template)
        return fig

    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output({"type": "index-averages-data-download-button", "index": MATCH}, "loading", allow_duplicate=True),
        Input({"type": "index-averages-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output({"type": "index-averages-data-download", "index": MATCH}, "data"),
        Output({"type": "index-averages-data-download-button", "index": MATCH}, "loading"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "index-averages-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_acoustic_indices",
            ctx.triggered_id["index"],
        ), False
