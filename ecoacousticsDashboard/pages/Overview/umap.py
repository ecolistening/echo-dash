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
from loguru import logger
from typing import (
    Any,
    Dict,
    List,
    Tuple,
)

from api import (
    dispatch,
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
graph_id = f"{PAGE_NAME}-graph"
colour_select_id = f"{PAGE_NAME}-colour-facet-select"
symbol_select_id = f"{PAGE_NAME}-symbol-facet-select"
row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
opacity_slider_id = f"{PAGE_NAME}-plot-options-opacity"
sample_slider_id = f"{PAGE_NAME}-plot-options-sample"
umap_hash_id = f"{PAGE_NAME}-hash"
plot_data_id = "plot-data"
plot_umap_data_id = "plot-data-umap"
download_dataframe_id = "download-dataframe"

layout = html.Div([
    dcc.Store(id=umap_hash_id),
    dcc.Store(id=plot_data_id),
    dcc.Store(id=plot_umap_data_id),
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
    ], grow=True),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "10px"}
    ),
    dmc.Grid([
        dmc.Col(html.Div([
            dmc.Text(
                "Opacity",
                size='sm',
                align="right",
            ),
            dmc.Slider(
                id=opacity_slider_id,
                min=0,
                max=100,
                step=5,
                value=50,
                marks=[
                    dict(value=i, label=f"{i}%")
                    for i in range(0, 101, 20)
                ],
                persistence=True,
            )
        ]), span=4),
        dmc.Col(html.Div([
            dmc.Text(
                "Sample Size",
                size="sm",
                align="right",
            ),
            dmc.Slider(
                id=sample_slider_id,
                persistence=True,
                min=1,
                value=None,
                step=1,
            )
        ]), span=4),
    ]),
    dmc.Divider(
        variant="dotted",
        style={"margin-top": "10px"}
    ),
    dcc.Loading(
        dcc.Graph(id=graph_id),
    ),
    dmc.Grid(
        children=[
            dmc.Col(html.Div([
                dmc.Title('About', order=2),
                dmc.Text('A UMAP is a way of projecting high-dimensional data onto fewer dimensions.'),
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
        ],
        gutter="xl",
    )
])

@callback(
    Output(sample_slider_id, 'max'),
    Output(sample_slider_id, 'value'),
    Output(sample_slider_id, 'marks'),
    Input(dataset_select_id, component_property='value'),
    Input(date_picker_id, component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, component_property='value'),
    State(sample_slider_id, component_property='value'),
)
def update_sample_slider(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    sample_size: int = None,
) -> Tuple[int, int, Dict[int, str]]:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"dataset={dataset_name} dates:{len(dates)} locations:{len(locations)} "
        f"{sample_size=} "
    )
    acoustic_features = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        default=[],
    )
    max_samples = len(acoustic_features)
    slider_ticks = np.linspace(1, max_samples, 5, endpoint=True, dtype=int)
    marks = [dict(value=i, label=f"{i}") for i in slider_ticks]
    sample_size = min(sample_size or max_samples, max_samples)
    return max_samples, sample_size, marks

@callback(
    Output(graph_id, "figure", allow_duplicate=True),
    # Output(plot_data_id, "data"),
    # Output(plot_umap_data_id, 'data'),
    # Output(umap_hash_id, "data", allow_duplicate=True),
    State(dataset_select_id, "value"),
    State(date_picker_id, 'value'),
    State({'type': 'checklist-locations-hierarchy', 'index': ALL}, "value"),
    Input(sample_slider_id, "value"),
    Input(colour_select_id, "value"),
    Input(symbol_select_id, "value"),
    Input(row_facet_select_id, "value"),
    Input(col_facet_select_id, "value"),
    prevent_initial_call=True,
)
def update_figure(
    dataset_name: str,
    dates: List[str],
    locations: List[str],
    sample_size: int,
    colour_by: str,
    symbol_by: str,
    row_facet: str,
    col_facet: str,
) -> Tuple[Any, ...]:
    logger.debug(
        f"Trigger ID={ctx.triggered_id}: "
        f"dataset={dataset_name} dates:{len(dates)} locations:{len(locations)} "
        f"{sample_size=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} "
    )

    acoustic_features, umap_data = dispatch(
        FETCH_ACOUSTIC_FEATURES_UMAP,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        default=pd.DataFrame({0: pd.Series(dtype=float), 1: pd.Series(float)}),
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )

    fig = px.scatter(
        umap_data,
        x=0,
        y=1,
        # opacity=opacity / 100.0,
        color=colour_by,
        symbol=symbol_by,
        facet_row=row_facet,
        facet_col=col_facet,
        category_orders=category_orders,
        hover_name='file',
        hover_data=['site', 'dddn', 'timestamp', 'path'],   # Path last for sound sample modal
        labels={'color': 'Site'},
        height=PLOT_HEIGHT,
    )

    # Add centered title
    fig.update_layout(
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )

    # data_tabular = data.to_json(date_format='iso', orient='table')
    # data_nested = data.to_json(date_format='iso', orient='split')

    # Select sample for audio modal
    # fig.update_layout(clickmode='event+select')

    # Adjust size of scatter dots
    # fig.update_traces(marker=dict(size=dot_size))

    return fig#, data_tabular, data_nested

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
def download_data(dataset_name, json_data, *args, **kwargs):
    logger.debug(
        f"Trigger ID={ctx.triggered_id}:"
        f"dataset={dataset_name} json data ({len(json_data)}B)"
    )
    return dispatch(SEND_DATA_FOR_DOWNLOAD, json_data, ctx.triggered_id)

# @callback(
#     Output(graph_id, "figure", allow_duplicate=True),
#     Output(f'{PAGE_NAME}-hash', component_property='data', allow_duplicate=True),

#     State('plot-data-umap', component_property='data'),
#     State(f'{PAGE_NAME}-hash', component_property='data'),

#     State('dataset-select', component_property='value'),
#     State('date-picker', component_property='value'),
#     State({'type': 'checklist-locations-hierarchy', 'index': ALL}, component_property='value'), 
#     State(sample_slider_id, component_property='value'),

#     Input(colour_select, component_property='value'),
#     Input(symbol_select, component_property='value'),
#     Input(row_facet_select, component_property='value'),
#     Input(col_facet_select, component_property='value'),
#     Input(size_slider, component_property='value'),
#     Input(opacity_slider_id, component_property='value'),

#     prevent_initial_call=True
# )
# def update_graph_visuals(json_data, hash, dataset_name, dates, locations, sample, colour_by, symbol_by, row_facet, col_facet, dot_size, opacity):
#     logger.debug(f"Trigger ID={ctx.triggered_id}: json data ({len(json_data)}B) {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=} {opacity=}")

#     new_hash = get_UMAP_hash(dataset_name, dates, locations, sample, colour_by, symbol_by, row_facet, col_facet, dot_size, opacity)
#     if hash == new_hash:
#         logger.debug("No new hash value, return.")
#         return no_update, no_update

#     graph_data = pd.read_json(StringIO(json_data), orient='split')

#     dataset = dataset_loader.get_dataset(dataset_name)
#     # Revert automatic formatting
#     graph_data['date'] = graph_data['date'].astype(str)

#     for opt in DatasetDecorator(dataset).drop_down_select_options():
#         if opt['group'] == 'Site Level':
#             feat_name = opt['value']
#             graph_data[feat_name] = graph_data[feat_name].astype(str)

#     fig = get_UMAP_fig(graph_data, dataset_name, colour_by, symbol_by, row_facet, col_facet, dot_size, opacity)

#     return fig, new_hash


# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#         Cache         #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

# @lru_cache(maxsize=2) #Just keep one per dataset
# def get_idx_data_lru(dataset_name: str, dates:tuple, locations:tuple):
#     dataset = dataset_loader.get_dataset(dataset_name)
#     return dataset.umap_acoustic_features

# # ~~~~~~~~~~~~~~~~~~~~~ #
# #                       #
# #       Functions       #
# #                       #
# # ~~~~~~~~~~~~~~~~~~~~~ #

# def get_idx_data(dataset_name, dates, locations):
#     return get_idx_data_lru(str(dataset_name), list2tuple(dates), list2tuple(locations))

# def get_graph_data(idx_data, sample):
#     # Random Sample
#     if sample < idx_data.shape[0]:
#         logger.debug(f"Select {sample}/{idx_data.shape[0]} random samples..")
#         sel_data = idx_data.sample(n=sample, axis=0)
#     else:
#         sel_data = idx_data

#     graph_data = dataset.umap_acoustic_features # umap_data(sel_data)

#     logger.debug(f"Return graph data and selected samples.")
#     return graph_data, sel_data

# def get_UMAP_hash(dataset_name, dates, locations, sample, colour_by, symbol_by, row_facet, col_facet, dot_size, opacity):
#     string = "-".join(str(v) for v in (dataset_name, dates, locations, sample, colour_by, symbol_by, row_facet, col_facet, dot_size, opacity))
#     return str(hash(string))

# def get_UMAP_fig(graph_data, dataset_name, colour_by, symbol_by, row_facet, col_facet, dot_size, opacity):

#     logger.debug(f"Generate UMAP plot for graph data {graph_data.shape} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=} {opacity=}")    

#     dataset = dataset_loader.get_dataset(dataset_name)

#     fig = px.scatter(
#         graph_data, x=0, y=1,
#         opacity=opacity / 100.0,
#         color=colour_by,
#         symbol=symbol_by,
#         facet_row=row_facet,
#         facet_col=col_facet,
#         category_orders=DatasetDecorator(dataset).category_orders(),
#         hover_name='file',
#         hover_data=['site', 'dddn', 'timestamp', 'path'],   # Path last for sound sample modal
#         # labels={'color': 'Site'},
#         height=PLOT_HEIGHT
#     )

#     # Add centered title
#     fig.update_layout(title={'text':PAGE_TITLE,
#                              'x':0.5,
#                              'y':0.97,
#                              'font':{'size':24}
#                              })

#     # Select sample for audio modal
#     fig.update_layout(clickmode='event+select')

#     # Adjust size of scatter dots
#     fig.update_traces(marker=dict(size=dot_size))

#     return fig
