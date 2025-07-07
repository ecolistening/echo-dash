import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import pandas as pd

from dash import callback, dcc, html, ctx
from dash import Output, Input, State
from dash import MATCH
from dash import exceptions
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
)
from utils import audio_bytes_to_enc
from utils.webhost import AudioAPI

PAGE_LIMIT = 10

def FileSelectionSidebar(
    span: int = 4
) -> dmc.GridCol:
    style_hidden = dict(display="none")
    style_visible = dict(display="block")

    component = dmc.GridCol(
        id=f"umap-toggle-sidebar",
        span=0,
        style=style_hidden,
        children=html.Div([
            dcc.Store(id="umap-sidebar-file-data"),
            dmc.Stack(
                style={"margin-top": "1rem"},
                children=[
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Button(
                                "Filter Selected",
                                id="selection-sidebar-filter-disclude-button",
                                variant="light",
                                color="red",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Filter Remaining",
                                id="selection-sidebar-filter-include-button",
                                variant="light",
                                color="red",
                                n_clicks=0,
                            ),
                        ]
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Text(
                                id="selection-sidebar-files-count",
                                size="sm",
                            ),
                        ],
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Pagination(
                                id="selection-sidebar-files-pagination",
                                total=1,
                                value=1,
                                size="sm",
                                color="indigo",
                            ),
                        ],
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Accordion(
                                id="selection-sidebar-files-accordion",
                                chevronPosition="right",
                                value=[],
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ]),
    )

    @callback(
        Output("graph-container", "span"),
        Output("umap-toggle-sidebar", "span"),
        Output("umap-toggle-sidebar", "style"),
        Output("umap-sidebar-file-data", "data"),
        Output("selection-sidebar-files-count", "children", allow_duplicate=True),
        Output("selection-sidebar-files-pagination", "total"),
        State("dataset-select", "value"),
        Input("umap-graph", "selectedData"),
        prevent_initial_call=True,
    )
    def toggle_selection_sidebar(
        dataset_name: str,
        selected_data: Dict[str, Any],
    ) -> Tuple[int, int, Dict[str, str], str, str, int]:
        if selected_data is None or len((points := selected_data['points'])) == 0:
            return (
                graph_container_span := 12,
                sidebar_span := 0,
                sidebar_style := style_hidden,
                selected_data_json := "",
                selected_text := "",
                total_pages := 1,
            )
        logger.debug(
            f"Trigger ID={ctx.triggered_id}: "
            f"selected={len(points)} {dataset_name=}"
        )
        data = dispatch(
            FETCH_FILES,
            dataset_name=dataset_name,
            file_ids=[
                point["hovertext"] # file_id should be the hover text
                for point in points
            ],
        )

        total = len(data)
        start = 1
        end = min(total, PAGE_LIMIT * start)

        return (
            graph_container_span := 12 - span,
            sidebar_span := span,
            sidebar_style := style_visible,
            selected_data_json := data.to_json(date_format="iso", orient="table"),
            selected_text := f"Showing {start} - {end} / {total}",
            total_pages := (total + PAGE_LIMIT - 1) // PAGE_LIMIT,
        )

    @callback(
        Output("selection-sidebar-files-accordion", "children"),
        Output("selection-sidebar-files-count", "children", allow_duplicate=True),
        State("umap-sidebar-file-data", "data"),
        Input("selection-sidebar-files-pagination", "value"),
        Input("selection-sidebar-files-pagination", "total"),
        prevent_initial_call=True,
    )
    def change_page(
        json_data: str,
        current_page: int,
        total_pages: int,
    ) -> html.Div:
        if json_data == "" or json_data is None:
            return (
                accordion := html.Div(),
                selected_text := "",
            )

        data = pd.read_json(StringIO(json_data), orient="table")
        page_data = data.iloc[(current_page - 1):(current_page - 1) + PAGE_LIMIT]

        logger.debug(
            f"Trigger ID={ctx.triggered_id}: "
            f"{current_page=} selected={len(page_data)}"
        )

        accordion = html.Div([
            dmc.AccordionItem(
                value=row["file_id"],
                children=[
                    dmc.AccordionControl(row["file_name"]),
                    dmc.AccordionPanel(
                        html.Div(
                            id={"type": "selection-sidebar-file-data", "index": row["file_id"]},
                            children=[],
                        )
                    )
                ]
            )
            for _, row in page_data.iterrows()
        ])

        total = len(data)
        start = PAGE_LIMIT * (current_page - 1) + 1
        end = min(total, PAGE_LIMIT * current_page)
        selected_text = f"Showing {start} - {end} / {total}",

        return accordion, selected_text

    @callback(
        Output({"type": "selection-sidebar-file-data", "index": MATCH}, "children"),
        State("dataset-select", "value"),
        State("umap-sidebar-file-data", "data"),
        State({"type": "selection-sidebar-file-data", "index": MATCH}, "id"),
        Input("selection-sidebar-files-accordion", "value"),
        prevent_initial_call=True,
    )
    def toggle_file_panel(
        dataset_name: str,
        json_data: str,
        matched: str,
        open_values: str,
    ) -> html.Div:
        if (file_id := matched["index"]) not in open_values:
            raise exceptions.PreventUpdate

        data = pd.read_json(StringIO(json_data), orient="table").set_index("file_id")

        file_info = data.loc[file_id]
        audio_bytes, mime_type, _ = AudioAPI.get_audio_bytes(file_info.file_path, dataset_name)
        return html.Div([
            dcc.Loading(
                html.Audio(
                    id="audio-player",
                    src=audio_bytes_to_enc(audio_bytes, mime_type),
                    controls=True
                ),
            )
        ])

    @callback(
        Output("selection-sidebar-filter-include-button", "n_clicks"),
        Input("selection-sidebar-filter-include-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def include_file_selection(
        n_clicks: int,
    ) -> str:
        # TODO: include filter means adding all other file_ids to the store
        logger.debug("clicked", n_clicks)
        return n_clicks

    @callback(
        Output("selection-sidebar-filter-disclude-button", "n_clicks"),
        Input("selection-sidebar-filter-disclude-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def disclude_file_selection(
        n_clicks: int,
    ) -> str:
        # TODO: disclude filter means adding these file_ids to the store
        logger.debug("clicked", n_clicks)
        return n_clicks

    return component
