import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, ctx, no_update, clientside_callback
from dash import Output, Input, State, ALL, MATCH
from loguru import logger
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_LOCATIONS
from utils import capitalise_each, send_download
from utils.sketch import default_layout

ROWS_PER_PAGE = 20
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
    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="site",
        hover_data=['timezone'],
        color_discrete_sequence=["red"],
        zoom=zoom,
    )
    return fig

def Table(data: pd.DataFrame, caption: str = "") -> dmc.Table:
    return dmc.Table([
        dmc.TableThead(
            dmc.TableTr([
                dmc.TableTh(capitalise_each(col.replace("_", " ")))
                for col in data.columns
            ])
        ),
        dmc.TableTbody([
            dmc.TableTr([
                dmc.TableTd(record[col])
                for col in data.columns
            ])
            for record in data.sort_values(by="location").to_dict(orient="records")
        ]),
        dmc.TableCaption(caption)
    ])

def register_callbacks():
    @callback(
        Output("locations-table-container", "children"),
        Output("locations-paginated", "total"),
        Input("dataset-select", "value"),
        Input("locations-paginated", "value"),
        Input("locations-search", "value"),
    )
    def build_paginated_table(
        dataset_name: str,
        page: int,
        search_term: str,
    ) -> Table:
        data = fetch_data(dataset_name).sort_values(by="location").drop("site", axis=1)
        if search_term:
            search_term = search_term.lower()
            mask = data.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)
            data = data[mask]
        total = (len(data) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
        start = (page - 1) * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        paged_data = data.iloc[start:end]
        return Table(data=paged_data, caption="Location metadata"), total

    @callback(
        Output("map-graph", "figure"),
        Input("dataset-select", "value"),
        Input("map-style-select", "value"),
    )
    def update_graph(
        dataset_name: str,
        map_style: str
    ) -> go.Figure:
        data = fetch_data(dataset_name).sort_values(by="location")
        fig = plot(data)
        # fig.update_traces(cluster=dict(
        #     enabled=True,
        #     maxzoom=12,
        # ))
        fig.update_layout(default_layout(fig))
        fig.update_layout(map_style=map_style, margin=dict(r=0, t=0, l=0, b=0),)
        # this prevents the zoom from resetting after the map style is changed
        fig['layout']['uirevision'] = 'some-constant'
        return fig

    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output({"type": "map-data-download-button", "index": MATCH}, "loading", allow_duplicate=True),
        Input({"type": "map-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output({"type": "map-data-download", "index": MATCH}, "data"),
        Output({"type": "map-data-download-button", "index": MATCH}, "loading"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        State({"type": "map-data-download-button", "index": MATCH}, "id"),
        Input({"type": "map-data-download-button", "index": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        ids,
        clicks,
    ) -> Dict[str, Any]:
        if ids is None or not len(list(filter(None, ids))):
            return no_update
        return send_download(
            fetch_data(dataset_name).sort_values(by="location"),
            f"{dataset_name}_map_locations",
            ctx.triggered_id["index"],
        ), False
