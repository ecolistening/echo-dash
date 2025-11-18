import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_DATASET_OPTIONS, FETCH_FILE_WEATHER
from api import FETCH_DATASET_OPTIONS, FETCH_DATASET_CATEGORY_ORDERS
from api import filter_dict_to_tuples
from utils import list2tuple, send_download, safe_category_orders
from utils.sketch import default_layout

PLOT_HEIGHT = 800

def fetch_data(dataset_name, filters):
    action = FETCH_FILE_WEATHER
    payload = dict(dataset_name=dataset_name, **filter_dict_to_tuples(filters))
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def register_callbacks():
    @callback(
        Output("weather-hourly-graph", "figure"),
        State("dataset-select", "value"),
        Input("filter-store", "data"),
        Input("weather-hourly-variable-select", "value"),
        Input("weather-hourly-time-aggregation", "value"),
        Input("weather-hourly-colour-select", "value"),
        Input("weather-hourly-facet-row-select", "value"),
        Input("weather-hourly-year-wrap-checkbox", "checked"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        variable: str,
        time_agg: str,
        color: str,
        facet_row: str,
        annual_wrap: bool,
    ) -> go.Figure:
        options = dispatch(FETCH_DATASET_OPTIONS, dataset_name=dataset_name)
        category_orders = dispatch(FETCH_DATASET_CATEGORY_ORDERS, dataset_name=dataset_name)
        data = fetch_data(dataset_name, filters)

        if annual_wrap:
            data["_time"] = data["nearest_hour"].apply(lambda dt: dt.replace(year=1972))
            x_tick_format = "%b"
        else:
            data["_time"] = data["nearest_hour"]
            x_tick_format = "%b %Y"

        data = (
            data[data.variable == variable]
            .drop_duplicates(["_time", "site_id"])
            .sort_values("_time")
            .groupby(list(set(filter(None, [color, facet_row, pd.Grouper(key="_time", freq=time_agg)]))))
            .agg(value_mean=("value", "mean"), value_std=("value", "std"))
            .reset_index()
        )

        fig = px.line(
            data_frame=data,
            x="_time",
            y="value_mean",
            error_y="value_std",
            color=color,
            facet_row=facet_row,
            markers=True,
            labels={
                "_time": "Time",
                "value_mean": "Value",
                color: options.get(color, {}).get("label", color),
                facet_row: options.get(facet_row, {}).get("label", facet_row),
            },
            category_orders=safe_category_orders(data, category_orders),
        )

        fig.update_traces(marker=dict(size=4))
        fig.update_xaxes(tickformat=x_tick_format)
        fig.update_layout(default_layout(fig))
        fig.update_layout(title_text=options.get(variable, {}).get("label", variable))
        return fig

    @callback(
        Output("weather-hourly-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "weather-hourly-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_weather",
            ctx.triggered_id["index"]
        )
