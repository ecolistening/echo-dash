import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_LOCATIONS
from utils import capitalise_each, send_download

PLOT_HEIGHT = 800

def fetch_data(dataset_name):
    action = FETCH_LOCATIONS
    payload = dict(dataset_name=dataset_name)
    logger.debug(f"{ctx.triggered_id=} {action=} {payload=}")
    return dispatch(action, **payload)

def plot(df):
    # calculate Zoom Level for World Map, https://docs.mapbox.com/help/glossary/zoom-level/#zoom-levels-and-geographical-distance
    extents = df.describe()
    longitude_range = extents.loc['max', 'longitude'] - extents.loc['min', 'longitude']
    latitude_range = extents.loc['max', 'latitude'] - extents.loc['min', 'latitude']
    # The 111 is a constant to convert decimal degrees to kilometers
    max_bound = max(longitude_range, latitude_range) * 111
    # determine a zoom level
    zoom = 12 - np.log(max_bound)*1.1
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="site",
        hover_data=['timezone'],
        color_discrete_sequence=["red"],
        zoom=zoom,
    )
    fig.update_layout(
        height=PLOT_HEIGHT,
        margin=dict(r=0, t=0, l=0, b=0),
        mapbox_style="open-street-map",
    )
    return fig

def Table(data: pd.DataFrame, caption: str = "") -> dmc.Table:
    return dmc.Table([
        dmc.TableThead(
            dmc.TableTr([dmc.TableTh(capitalise_each(col.replace("_", " "))) for col in data.columns])
        ),
        dmc.TableTbody([
            dmc.TableTr([dmc.TableTd(record[col]) for col in data.columns])
            for record in data.sort_values(by="location").to_dict(orient="records")
        ]),
        dmc.TableCaption(caption)
    ])

def register_callbacks():
    @callback(
        Output("map-page-info", "is_open"),
        Input("info-icon", "n_clicks"),
        State("map-page-info", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
        return not is_open

    @callback(
        Output("locations-table", "children"),
        Input("dataset-select", "value"),
    )
    def render_locations_table(dataset_name):
        data = fetch_data(dataset_name)
        return Table(data=data, caption="Location metadata")

    @callback(
        Output("map-graph", "figure"),
        Input("dataset-select", "value"),
    )
    def update_graph(dataset_name):
        data = fetch_data(dataset_name).sort_values(by="location")
        fig = plot(data)
        return fig

    @callback(
        Output("map-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "map-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name).sort_values(by="location"),
            f"{dataset_name}_map_locations",
            ctx.triggered_id["index"],
        )
