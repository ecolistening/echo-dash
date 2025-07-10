import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import pandas as pd

from dash import callback, dcc, html, ctx, no_update
from dash import Output, Input, State
from dash import MATCH
from dash import exceptions
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_FILES, FETCH_DATASET_CONFIG
from utils import audio_bytes_to_enc
from utils.webhost import AudioAPI

PAGE_LIMIT = 10

def FileSelectionSidebar(
    graph_id: str,
    graph_container_id: str,
    filter_store_id: str,
    span: int = 4
) -> dmc.GridCol:
    style_hidden = {
        "display":"none",
        "margin-top": "1rem",
        "border-left": "1px solid var(--mantine-color-gray-3)",
        "padding-left": "1rem",
    }
    style_visible = {
        "display": "block",
        "margin-top": "1rem",
        "border-left": "1px solid var(--mantine-color-gray-3)",
        "padding-left": "1rem",
    }

    component = dmc.GridCol(
        id="file-sidebar",
        span=0,
        style=style_hidden,
        children=html.Div([
            dcc.Store(id="file-sidebar-store"),
            dmc.Stack(
                m="1rem",
                children=[
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Button(
                                "Filter",
                                id="file-sidebar-disclude-button",
                                leftSection=DashIconify(icon="f7:delete-left-fill"),
                                variant="light",
                                color="red",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Zoom",
                                id="file-sidebar-include-button",
                                leftSection=DashIconify(icon="cil:zoom"),
                                variant="light",
                                color="blue",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Reset",
                                id="file-sidebar-reset-button",
                                leftSection=DashIconify(icon="fluent:arrow-reset-20-filled"),
                                variant="light",
                                color="green",
                                n_clicks=0,
                            ),
                            dmc.Box(
                                style={
                                    "padding": "1rem",
                                    "display": "flex",
                                    "align-content": "center",
                                    "justify-content": "right",
                                },
                                children=dmc.ActionIcon(
                                    DashIconify(
                                        icon="system-uicons:cross",
                                        width=24,
                                    ),
                                    id="file-close-sidebar",
                                    variant="light",
                                    size="lg",
                                    n_clicks=0,
                                ),
                            )
                        ]
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Text(
                                id="file-sidebar-files-count",
                                size="sm",
                            ),
                        ],
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Pagination(
                                id="file-sidebar-files-pagination",
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
                                id="file-sidebar-files-accordion",
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
        Output(graph_container_id, "span", allow_duplicate=True),
        Output("file-sidebar", "span", allow_duplicate=True),
        Output("file-sidebar", "style", allow_duplicate=True),
        State("file-sidebar", "style"),
        Input("file-close-sidebar", "n_clicks"),
        Input("toggle-file-sidebar", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_selection_sidebar(
        current_style: Dict[str, str],
        close: int,
        n_clicks: int,
    ) -> Tuple[int, int, Dict[str, str]]:
        if current_style == style_visible:
            return (
                graph_container_span := 12,
                sidebar_span := 0,
                sidebar_style := style_hidden,
            )
        return (
            graph_container_span := 12 - span,
            sidebar_span := span,
            sidebar_style := style_visible,
        )

    @callback(
        Output(graph_container_id, "span", allow_duplicate=True),
        Output("file-sidebar", "span", allow_duplicate=True),
        Output("file-sidebar", "style", allow_duplicate=True),
        Output("file-sidebar-store", "data"),
        Output("file-sidebar-files-count", "children", allow_duplicate=True),
        Output("file-sidebar-files-pagination", "total"),
        State("dataset-select", "value"),
        State("file-sidebar", "span"),
        State("file-sidebar", "style"),
        Input(graph_id, "selectedData"),
        prevent_initial_call=True,
    )
    def toggle_selection_sidebar(
        dataset_name: str,
        current_span: int,
        current_style: Dict[str, str],
        selected_data: Dict[str, Any],
    ) -> Tuple[int, int, Dict[str, str], str, str, int]:
        if selected_data is None or len((points := selected_data['points'])) == 0:
            return (
                graph_container_span := 12 - current_span,
                sidebar_span := current_span,
                sidebar_style := current_style,
                selected_data_json := "",
                selected_text := "",
                total_pages := 1,
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
        Output("file-sidebar-files-accordion", "children"),
        Output("file-sidebar-files-count", "children", allow_duplicate=True),
        State("file-sidebar-store", "data"),
        Input("file-sidebar-files-pagination", "value"),
        Input("file-sidebar-files-pagination", "total"),
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
                            id={"type": "file-sidebar-file-data", "index": row["file_id"]},
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
        Output({"type": "file-sidebar-file-data", "index": MATCH}, "children"),
        State("dataset-select", "value"),
        State("file-sidebar-store", "data"),
        State({"type": "file-sidebar-file-data", "index": MATCH}, "id"),
        Input("file-sidebar-files-accordion", "value"),
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

        config = dispatch(FETCH_DATASET_CONFIG, dataset_name=dataset_name)
        data = pd.read_json(StringIO(json_data), orient="table").set_index("file_id")

        file_info = data.loc[file_id]
        audio_bytes, mime_type, _ = AudioAPI.get_audio_bytes(file_info.file_path, dataset_name, config)
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
        Output(filter_store_id, "data", allow_duplicate=True),
        # TODO: we need access to the whole plot data
        State("file-sidebar-store", "data"),
        State(filter_store_id, "data"),
        Input("file-sidebar-include-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def include_file_selection(
        json_data: str,
        filtered_file_ids: Dict[str, Any],
        n_clicks: int,
    ) -> str:
        """
        Include filter means adding all other file_ids to the store
        """
        if not n_clicks: return no_update
        # filtered_file_ids = frozenset((filtered_file_ids or {}).keys())
        # file_ids = set(pd.read_json(StringIO(json_data), orient="table")["file_id"].tolist())
        # TODO
        # return dict(zip(file_ids, [1 for _ in range(len(file_ids))]))
        return {}

    @callback(
        Output(filter_store_id, "data", allow_duplicate=True),
        State("file-sidebar-store", "data"),
        State(filter_store_id, "data"),
        Input("file-sidebar-disclude-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def disclude_file_selection(
        json_data: str,
        filtered_file_ids: Dict[str, Any],
        n_clicks: int,
    ) -> str:
        """
        Include filter means adding all other file_ids to the store
        """
        if not n_clicks: return no_update
        filtered_file_ids = frozenset((filtered_file_ids or {}).keys())
        file_ids = set(pd.read_json(StringIO(json_data), orient="table")["file_id"].tolist())
        file_ids = filtered_file_ids.union(file_ids)
        return dict(zip(file_ids, [1 for _ in range(len(file_ids))]))

    @callback(
        Output(filter_store_id, "data", allow_duplicate=True),
        State(filter_store_id, "data"),
        Input("file-sidebar-reset-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_file_selection(
        filtered_file_ids: Dict[str, Any],
        n_clicks: int,
    ) -> str:
        """
        Include filter means adding all other file_ids to the store
        """
        if not n_clicks: return no_update
        return {}

    return component
