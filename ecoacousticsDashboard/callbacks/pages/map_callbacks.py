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
from utils import capitalise_each

PLOT_HEIGHT = 800

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
        data = dispatch(FETCH_LOCATIONS, dataset_name=dataset_name).sort_values(by="location")
        return dmc.Table([
            dmc.TableThead(
                dmc.TableTr([dmc.TableTh(capitalise_each(col.replace("_", " "))) for col in data.columns])
            ),
            dmc.TableTbody([
                dmc.TableTr([dmc.TableTd(record[col]) for col in data.columns])
                for record in data.to_dict(orient="records")
            ]),
            dmc.TableCaption("Location metadata")
        ])

    @callback(
        Output("map-graph", "figure"),
        Input("dataset-select", "value"),
    )
    def update_graph(dataset_name):
        logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=}")

        data = dispatch(
            FETCH_LOCATIONS,
            dataset_name=dataset_name,
        )
        '''
            Calculate Zoom Level for World Map

            https://docs.mapbox.com/help/glossary/zoom-level/#zoom-levels-and-geographical-distance
        '''
        extents = data.describe()
        longitude_range = extents.loc['max', 'longitude'] - extents.loc['min', 'longitude']
        latitude_range = extents.loc['max', 'latitude'] - extents.loc['min', 'latitude']

        # The 111 is a constant to convert decimal degrees to kilometers
        max_bound = max(longitude_range, latitude_range) * 111

        # Formula established by trial-and-error
        zoom = 12 - np.log(max_bound)*1.1

        logger.debug(f"{dataset_name=} {latitude_range=:.4f} {longitude_range=:.4f} {max_bound=:.4f} {np.log(max_bound)=:.4f} {zoom=:.4f}")

        fig = px.scatter_mapbox(
            data,
            lat="latitude",
            lon="longitude",
            hover_name="site",
            hover_data=['timezone'],
            color_discrete_sequence=["red"],
            zoom=zoom,
        )

        fig.update_layout(
            height=PLOT_HEIGHT,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            mapbox_style="open-street-map",
        )

        return fig
