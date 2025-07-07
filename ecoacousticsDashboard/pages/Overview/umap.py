import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from dash import html, dcc, callback, Output, Input, ALL, MATCH, ctx, State, no_update
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import (
    Any,
    Dict,
    List,
    Tuple,
)

from api import (
    dispatch,
    FETCH_FILES,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_ACOUSTIC_FEATURES_UMAP,
    FETCH_DATASET_CATEGORIES,
)
from components.top_bar import TopBar
from components.file_selection_sidebar import FileSelectionSidebar

from utils import list2tuple

PAGE_NAME = "UMAP"
PAGE_TITLE = "UMAP of Soundscape Descriptors"
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=PAGE_NAME,
)

# Filter Methodology
# Approach 1:
# 1. A global filter stores a list of file_ids, an include list.
#    so this should be initialised to be the complete file list for the dataset
# 2. On each page, based on the file list, we fetch the actual data and a graph is rendered based on the selection
# 3. The global filter can be reset to all files via a reset button, or rescoped in the filters menu
#   - A single reset is easy to implement, just re-fetch all file data and reset the store
#   - Changing filters means storing the filter operation to be re-run, so building a composite query
#   - This is more challenging. We'd need some kind of smart filter parser since all the tables are stored separately

# Approach 2:
# 1. A global filter store is empty, a disclude list
# 2. Data is selected based on those that should be omitted, i.e. file_id not in file_ids
# 3. Resetting the global filter is simply emptying the store so all data points are fetched
# 4. Resetting a particular part of the store, for example date, requires:
#   - Checking those in the disclude list are within the new boundaries set **PROBLEM**: how do you know the source of where something was filtered? For example, suppose I select some points in UMAP, then apply a date filter, then change the dates, how do I know files were filtered by UMAP or by the date filter, if the dates overlapped?
#   - Adding to the disclude list those within that boundary

# Approach 3:
# 1. Each filter operation e.g. date, UMAP, weather, has its own unique store which contains a disclude list of file_ids
# 2. When updating a particular filter, simply change the omitted ids in the list.
# 3. Data is fetched by composing together all file_ids in the store, removing duplicates, and executing the query to fetch those that are not in the list

# plot params
colour_select_id = f"umap-colour-facet-select"
symbol_select_id = f"umap-symbol-facet-select"
row_facet_select_id = f"umap-row-facet-select"
col_facet_select_id = f"umap-col-facet-select"
opacity_slider_id = f"umap-plot-options-opacity"
size_slider_id = f"umap-size-slider"
category_orders_id = f"umap-category-orders"

# sidebar params
toggle_sidebar_id = f"umap-toggle-sidebar"
sidebar_file_data_id = f"umap-sidebar-file-data"

layout = html.Div([
    dcc.Store(id=category_orders_id),
    TopBar(
        PAGE_NAME,
        children=[
            # components.ColourSelect(
            #     id=colour_select_id,
            #     default=None,
            # ),
            # components.SymbolSelect(
            #     id=symbol_select_id,
            #     default=None,
            # ),
            # components.RowFacetSelect(
            #     id=row_facet_select_id,
            #     default=None,
            # ),
            # components.ColumnFacetSelect(
            #     id=col_facet_select_id,
            #     default=None,
            # ),
        ],
    ),
    dmc.Group([
        html.Div([
            dmc.Text(
                "Dot Size",
                size="sm",
                ta="left",
            ),
            dmc.Slider(
                id=size_slider_id,
                min=1,
                max=20,
                step=1,
                value=6,
                marks=[
                    {"value": i, "label": f"{i}"}
                    for i in (1, 10, 20)
                ],
                persistence=True
            )
        ]),
        html.Div([
            dmc.Text(
                "Opacity",
                size='sm',
                ta="left",
            ),
            dmc.Slider(
                id=opacity_slider_id,
                min=0,
                max=100,
                step=5,
                value=50,
                marks=[
                    dict(value=i, label=f"{i}%")
                    for i in np.linspace(0, 100, 5, endpoint=True, dtype=int)
                ],
                persistence=True,
            )
        ]),
        html.Div([
            dmc.Text(
                "Sample Size",
                size="sm",
                ta="left",
            ),
            dmc.Slider(
                id=f"umap-sample-slider",
                persistence=True,
                min=1,
                value=None,
                step=1,
            )
        ]),
    ], grow=True),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "30px"}
    ),
    # Note: this is slightly hacky but it works
    # the file selection sidebar changes the span of the
    # sibling column span to make itself visible
    dmc.Grid([
        dmc.GridCol(
            id="graph-container",
            span=12,
            children=[
                dcc.Loading([
                    dcc.Graph(id=f"umap-graph"),
                ]),
            ],
        ),
        FileSelectionSidebar(span=4),
    ]),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "10px"}
    ),
    dbc.Offcanvas(
        id="page-info",
        is_open=False,
        placement="bottom",
        children=dmc.Grid(
            children=[
                dmc.GridCol(
                    span=4,
                    children=[
                        dmc.Title(PAGE_TITLE, order=2),
                    ],
                ),
                dmc.Divider(
                    variant="dotted",
                    orientation="vertical"
                ),
                dmc.GridCol(
                    span="auto",
                    children=[
                        dmc.Text(
                            "UMAP is a method of projecting high-dimensional data onto fewer dimensions. "
                            "The axes themselves have no precise meaning, other than defining the distance "
                            "between the data points. ",
                            span=True,
                        ),
                        dmc.Anchor('[details]', href='https://pair-code.github.io/understanding-umap/', target="_blank"), # target="_blank" opens link in a new tab
                    ]
                ),
            ]
        ),
    ),
])

@callback(
    Output(f"umap-sample-slider", "max"),
    Output(f"umap-sample-slider", "value"),
    Output(f"umap-sample-slider", "marks"),
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
)
def init_slider(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
) -> str:
    # FIXME: to support Kilpis we need to fix this so its the total number of instances, i.e. file_segment_id
    # ideally this should be constructed in soundade during the index files stage
    files = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        default=[],
    )
    max_samples = len(files)
    sample_size = max_samples # min(1000, max_samples)
    ticks = [
        dict(value=i, label=f"{i}")
        for i in np.linspace(1, max_samples, 5, endpoint=True, dtype=int)
    ]
    return max_samples, sample_size, ticks

@callback(
    Output(f"umap-graph", "figure"),
    Input("dataset-select", "value"),
    Input("date-picker", "value"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input(f"umap-sample-slider", "value"),
    Input(f"umap-sample-slider", "max"),
    # Input(colour_select_id, "value"),
    # Input(symbol_select_id, "value"),
    # Input(row_facet_select_id, "value"),
    # Input(col_facet_select_id, "value"),
    Input(opacity_slider_id, "value"),
    Input(size_slider_id, "value"),
    Input(category_orders_id, "data"),
    prevent_initial_call=True,
)
def draw_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    sample_size: int,
    max_samples: int,
    # colour_by: str,
    # symbol_by: str,
    # row_facet: str,
    # col_facet: str,
    opacity: int,
    dot_size: int,
    category_orders: List[str] = [],
) -> go.Figure:
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        sample_size=max_samples, # ensures we subsample rather than re-run UMAP
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )

    fig = px.scatter(
        data.sample(sample_size),
        x="UMAP Dim 1",
        y="UMAP Dim 2",
        opacity=opacity / 100.0,
        # color=colour_by,
        # symbol=symbol_by,
        # facet_row=row_facet,
        # facet_col=col_facet,
        category_orders=category_orders,
        hover_name="file_id",
        hover_data=["file", "site", "dddn", "timestamp"],
        height=PLOT_HEIGHT,
    )

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    fig.update_traces(
        marker=dict(size=dot_size)
    )

    return fig
