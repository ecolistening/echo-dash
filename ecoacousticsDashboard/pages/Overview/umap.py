import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import plotly.express as px

from dash import (
    html,
    dcc,
    callback,
    Output,
    Input,
    ALL,
    ctx,
    State,
    no_update,
)
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
    SEND_DATA_FOR_DOWNLOAD,
)
import components

from utils import list2tuple
from utils.save_plot_fig import get_save_plot

PAGE_NAME = "UMAP"
PAGE_TITLE = "UMAP of Soundscape Descriptors"
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=PAGE_NAME,
)

dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
locations_hierarchy_id = {"type": "checklist-locations-hierarchy", "index": ALL}
graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-facet-select"
symbol_select_id = f"{PAGE_NAME}-symbol-facet-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
opacity_slider_id = f"{PAGE_NAME}-plot-options-opacity"
sample_slider_id = f"{PAGE_NAME}-plot-options-sample"
size_slider_id = f"{PAGE_NAME}-size-slider"
umap_hash_id = f"{PAGE_NAME}-hash"
category_orders_id = f"{PAGE_NAME}-category-orders"
plot_data_id = f"{PAGE_NAME}-plot-data"
download_dataframe_id = "download-dataframe"

layout = html.Div([
    dcc.Store(id=plot_data_id),
    dcc.Store(id=category_orders_id),
    dmc.Title(PAGE_TITLE, order=1),
    dmc.Divider(variant="dotted"),
    dmc.Group([
        components.ColourSelect(
            id=colour_select_id,
            default=None,
        ),
        components.SymbolSelect(
            id=symbol_select_id,
            default=None,
        ),
        components.RowFacetSelect(
            id=row_facet_select_id,
            default=None,
        ),
        components.ColumnFacetSelect(
            id=col_facet_select_id,
            default=None,
        ),
        components.SizeSlider(
            id=size_slider_id,
            default=3,
        ),
    ], grow=True),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "15px"}
    ),
    dmc.Group([
        html.Div([
            dmc.Text(
                "Opacity",
                size='sm',
                align="left",
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
                align="left",
            ),
            dmc.Slider(
                id=sample_slider_id,
                persistence=True,
                min=1,
                value=None,
                step=1,
            )
        ]),
    ], grow=True),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "15px"}
    ),
    dcc.Loading([
        dcc.Graph(id=graph_id),
    ]),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "10px"}
    ),
    dmc.Grid([
        dmc.Col(html.Div([
            dmc.Title('About', order=2),
            dmc.Text(
                "UMAP is a method of projecting high-dimensional data onto fewer dimensions. "
                "The axes themselves have no precise meaning, other than defining the distance "
                "between the data points."
            ),
            dmc.Anchor('[details]', href='https://pair-code.github.io/understanding-umap/', target="_blank"), # target="_blank" opens link in a new tab
        ]), span=4),
        dmc.Col(html.Div([
            dmc.Title('Download Data', order=2),
            dmc.Text('Download the data in the current plot. Select a format below.'),
            dmc.ButtonGroup([
                dmc.Button("csv", variant="filled", id='dl_csv'),
                dmc.Button("excel", variant="filled", id='dl_xls'),
                dmc.Button("json", variant="filled", id='dl_json'),
                dmc.Button("parquet", variant="filled", id='dl_parquet'),
            ]),
            dcc.Download(id=download_dataframe_id),
        ]), span=4),
        dmc.Col(html.Div([
            components.FigureDownloader(graph_id),
        ]), span=4),
    ], gutter="xl")
])

@callback(
    Output(plot_data_id, "data"),
    Output(category_orders_id, "data"),
    Output(sample_slider_id, "max"),
    Output(sample_slider_id, "value"),
    Output(sample_slider_id, "marks"),
    Input(dataset_select_id, "value"),
    Input(date_picker_id, "value"),
    Input(locations_hierarchy_id, "value"),
    prevent_initial_call=True,
)
def update_umap_data_store(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
) -> str:
    """
    First callback in the initial execution chain.

    - Fetches UMAP projection from API and caches client-side
    - Fetches the category orders from API and caches client-side
    - Resets the slider range, ticks and sample size to be the maximum (as per cached UMAP)

    This is done as a joint action since the slider is data dependent
    separating these out would trigger the figure to reload multiple times
    """
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
    data = dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        sample_size=max_samples,
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )
    json_data = data.to_json(
        date_format="iso",
        orient="table",
    )
    ticks = [
        dict(value=i, label=f"{i}")
        for i in np.linspace(1, max_samples, 5, endpoint=True, dtype=int)
    ]
    return json_data, category_orders, max_samples, max_samples, ticks

@callback(
    Output(graph_id, "figure"),
    Input(sample_slider_id, "value"),
    Input(colour_select_id, "value"),
    Input(symbol_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    Input(opacity_slider_id, "value"),
    Input(size_slider_id, "value"),
    Input(plot_data_id, "data"),
    Input(category_orders_id, "data"),
    prevent_initial_call=True,
)
def update_figure(
    sample_size: int,
    colour_by: str,
    symbol_by: str,
    row_facet: str,
    col_facet: str,
    opacity: int,
    dot_size: int,
    json_data: str | None = None,
    category_orders: List[str] = [],
) -> Tuple[Any, ...]:
    """
    Second callback in the initial execution chain.

    - Subsamples from the browser-side UMAP data (stored as JSON)
    - Fetches the cached category orders
    - Renders the figure
    """
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"{sample_size=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {opacity=} {dot_size=}"
    )

    data = pd.read_json(
        StringIO(json_data),
        orient="table",
    ).sample(sample_size)

    fig = px.scatter(
        data,
        x="UMAP Dim 1",
        y="UMAP Dim 2",
        opacity=opacity / 100.0,
        color=colour_by,
        symbol=symbol_by,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=category_orders,
        hover_name='file',
        hover_data=['site', 'dddn', 'timestamp', 'path'],   # Path last for sound sample modal
        height=PLOT_HEIGHT,
    )

    # removed because we already have the title at the top of the page
    # fig.update_layout(
    #     title=dict(
    #         text=PAGE_TITLE,
    #         x=0.5,
    #         y=0.97,
    #         font=dict(size=24),
    #     )
    # )

    # Select sample for audio modal
    # fig.update_layout(clickmode='event+select')

    fig.update_traces(
        marker=dict(size=dot_size)
    )

    return fig

@callback(
    Output(download_dataframe_id, "data"),
    State(dataset_select_id, "value"),
    State(plot_data_id, "data"),
    Input("dl_csv", "n_clicks"),
    Input("dl_xls", "n_clicks"),
    Input("dl_json", "n_clicks"),
    Input("dl_parquet", "n_clicks"),
    prevent_initial_call=True,
)
def download_data(
    dataset_name: str,
    json_data: Dict[str, Any],
) -> Dict[str, Any]:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}:"
        f"dataset={dataset_name} json data ({len(json_data)}B)"
    )
    return dispatch(
        SEND_DATA_FOR_DOWNLOAD,
        dataset_name=dataset_name,
        json_data=json_data,
        dl_type=ctx.triggered_id,
    )
