import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px

from dash import html, dcc, callback, Output, Input, ALL, MATCH, ctx, State
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

from utils import list2tuple, audio_bytes_to_enc
from utils.webhost import AudioAPI

PAGE_NAME = "UMAP"
PAGE_TITLE = "UMAP of Soundscape Descriptors"
PLOT_HEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=PAGE_NAME,
)

# global filters
dataset_select_id = "dataset-select"
date_picker_id = "date-picker"
locations_hierarchy_id = {"type": "checklist-locations-hierarchy", "index": ALL}

# plot params
graph_id = f"{PAGE_NAME}-graph"
plot_data_id = f"{PAGE_NAME}-plot-data"
colour_select_id = f"{PAGE_NAME}-colour-facet-select"
symbol_select_id = f"{PAGE_NAME}-symbol-facet-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
opacity_slider_id = f"{PAGE_NAME}-plot-options-opacity"
sample_slider_id = f"{PAGE_NAME}-plot-options-sample"
size_slider_id = f"{PAGE_NAME}-size-slider"
category_orders_id = f"{PAGE_NAME}-category-orders"

# export params
download_dataframe_id = "download-dataframe"

# sidebar params
toggle_sidebar_id = f"{PAGE_NAME}-toggle-sidebar"
sidebar_audio_id = f"{PAGE_NAME}-sidebar-audio"
sidebar_file_data_id = f"{PAGE_NAME}-sidebar-file-data"
sidebar_file_content_id = f"{PAGE_NAME}-sidebar-file-content"

layout = html.Div([
    dcc.Store(id=plot_data_id),
    dcc.Store(id=category_orders_id),
    dcc.Store(id=sidebar_file_data_id),
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
    ], gutter="xl"),
    dbc.Offcanvas(
        id=toggle_sidebar_id,
        children=html.Div([
            dmc.Title('Subselection', order=2),
            html.Div(
                id=sidebar_file_content_id,
                children=[]
            )
        ]),
        is_open=False,
        placement="end",
        backdrop=False,
    )
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

    This is a joint action since separating these events independently triggers multiple redraw events
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
    sample_size = max_samples # min(1000, max_samples)
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
    return json_data, category_orders, max_samples, sample_size, ticks

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
        hover_name="file_id",
        hover_data=["file", "site", "dddn", "timestamp"],
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

@callback(
    Output(toggle_sidebar_id, "is_open"),
    Output(sidebar_file_data_id, "data"),
    State(dataset_select_id, "value"),
    Input(graph_id, "selectedData"),
    prevent_initial_call=True,
)
def toggle_selection_sidebar(
    dataset_name: str,
    selected_data: Dict[str, Any],
) -> bool:
    logger.debug(selected_data)
    if selected_data is None or len(selected_data['points']) == 0:
        return False, ""
    file_ids = [point["hovertext"] for point in selected_data["points"]]
    json_data = dispatch(
        FETCH_FILES,
        dataset_name=dataset_name,
        file_ids=file_ids,
    ).to_json(
        date_format="iso",
        orient="table",
    )
    return True, json_data

@callback(
    Output(sidebar_file_content_id, "children"),
    State(dataset_select_id, "value"),
    Input(sidebar_file_data_id, "data"),
    prevent_initial_call=True,
)
def update_sidebar_file_content(
    dataset_name: str,
    json_data: str,
) -> bool:
    if not len(json_data):
        return html.Div()

    data = pd.read_json(StringIO(json_data), orient="table")

    kids = [
        dmc.Accordion(
            id="files-accordion",
            chevronPosition="right",
            children=[
                dmc.AccordionItem(
                    value=str(i),
                    children=[
                        dmc.AccordionControl(file_data.file_name),
                        # dmc.AccordionPanel(
                        #     html.Audio(
                        #         id={ "type": "audio-player", "index": file_id },
                        #         src="",
                        #         controls=True,
                        #     )
                        # )
                    ]
                )
            ]
        )
        for i, (file_id, file_data) in enumerate(data.iterrows())
    ]

    return dmc.Accordion(
        chevronPosition="right",
        children=[
            dmc.AccordionItem(
                value="files",
                children=[
                    dmc.AccordionControl("Files"),
                    dmc.AccordionPanel(kids)
                ]
            )
        ]
    )

# @callback(
#     Output({ "type": "audio-player", "index": MATCH }, "src"),
#     State(dataset_select_id, "value"),
#     State(sidebar_file_data_id, "data"),
#     State({ "type": "audio-player", "index": MATCH }, "id"),
#     Input("files-accordion", "value"),
#     prevent_initial_call=True,
# )
# def update_audio_src(
#     dataset_name: str,
#     json_data: str,
#     audio_id: Dict[str, str],
#     open_value: str,
# ) -> str:
#     if not len(json_data):
#         return html.Div()

#     data = pd.read_json(StringIO(json_data), orient="table")

#     if open_value == audio_id["index"]:
#         row = data.loc[open_value]
#         audio_bytes, file_type, audio_path = AudioAPI.get_audio_bytes(row.file_path, dataset)
#         return audio_bytes_to_enc(audio_bytes, file_type)
#     return ""
