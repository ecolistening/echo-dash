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

from api import dispatch, FETCH_FILES
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
            dmc.Divider(
                variant="solid",
                orientation="vertical",
            ),
            dmc.Stack(
                style={"margin-top": "1rem"},
                children=[
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Button(
                                "Filter",
                                id="selection-sidebar-filter-disclude-button",
                                leftSection=DashIconify(icon="f7:delete-left-fill"),
                                variant="light",
                                color="red",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Zoom",
                                id="selection-sidebar-filter-include-button",
                                leftSection=DashIconify(icon="cil:zoom"),
                                variant="light",
                                color="blue",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Reset",
                                id="selection-sidebar-filter-reset-button",
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
                                    id="umap-close-sidebar",
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
        Output("graph-container", "span", allow_duplicate=True),
        Output("umap-toggle-sidebar", "span", allow_duplicate=True),
        Output("umap-toggle-sidebar", "style", allow_duplicate=True),
        State("umap-toggle-sidebar", "style"),
        Input("umap-close-sidebar", "n_clicks"),
        Input("toggle-file-selection-sidebar", "n_clicks"),
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
        Output("graph-container", "span", allow_duplicate=True),
        Output("umap-toggle-sidebar", "span", allow_duplicate=True),
        Output("umap-toggle-sidebar", "style", allow_duplicate=True),
        Output("umap-sidebar-file-data", "data"),
        Output("selection-sidebar-files-count", "children", allow_duplicate=True),
        Output("selection-sidebar-files-pagination", "total"),
        State("dataset-select", "value"),
        State("umap-toggle-sidebar", "span"),
        State("umap-toggle-sidebar", "style"),
        Input("umap-graph", "selectedData"),
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
        Output("umap-filter-store", "data", allow_duplicate=True),
        # TODO: we need access to the whole plot data
        State("umap-sidebar-file-data", "data"),
        State("umap-filter-store", "data"),
        Input("selection-sidebar-filter-include-button", "n_clicks"),
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
        Output("umap-filter-store", "data", allow_duplicate=True),
        State("umap-sidebar-file-data", "data"),
        State("umap-filter-store", "data"),
        Input("selection-sidebar-filter-disclude-button", "n_clicks"),
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
        Output("umap-filter-store", "data", allow_duplicate=True),
        State("umap-filter-store", "data"),
        Input("selection-sidebar-filter-reset-button", "n_clicks"),
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
