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
    dataset_id: str,
    graph_id: str,
    graph_container_id: str,
    sidebar_id: str,
    data_store_id: str,
    span: int = 4,
) -> dmc.Col:
    """
    A toggleable sidebar alongside a graph. Provides a paginated list of files and
    a button to add to a global filter to adjust the data currently in view (and for export)
    """
    filter_store = dcc.Store(id="filter-store")
    filter_button_id = "filter-button"

    files_pagination_id = "files-pagination"
    files_count_id = "files-count"
    files_accordion_id = "selection-sidebar-files-accordion"

    @callback(
        Output(graph_container_id, "span"),
        Output(sidebar_id, "span"),
        Output(sidebar_id, "style"),
        Output(data_store_id, "data"),
        Output(files_count_id, "children"),
        Output(files_pagination_id, "total"),
        State(dataset_id, "value"),
        Input(graph_id, "selectedData"),
        prevent_initial_call=True,
    )
    def toggle_selection_sidebar(
        dataset_name: str,
        selected_data: Dict[str, Any],
    ) -> Tuple[bool, str, html.Div, str]:
        if selected_data is None or len((points := selected_data['points'])) == 0:
            return (
                graph_container_span := 12,
                sidebar_span := 0,
                sidebar_style := {"display": "none"},
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

        return (
            graph_container_span := 12 - span,
            sidebar_span := span,
            sidebar_style := {"display": "block"},
            selected_data_json := data.to_json(date_format="iso", orient="table"),
            selected_text := f"{len(data)} selected...",
            total_pages := (len(data) + PAGE_LIMIT - 1) // PAGE_LIMIT,
        )

    @callback(
        Output(files_accordion_id, "children"),
        State(data_store_id, "data"),
        Input(files_pagination_id, "page"),
        Input(files_pagination_id, "total"),
        prevent_initial_call=True,
    )
    def change_page(
        json_data: str,
        current_page: int,
        total_pages: int,
    ) -> html.Div:
        if json_data == "" or json_data is None:
            return html.Div()

        data = pd.read_json(StringIO(json_data), orient="table")
        page_data = data.iloc[(current_page - 1):(current_page - 1) + PAGE_LIMIT]

        logger.debug(
            f"Trigger ID={ctx.triggered_id}: "
            f"{current_page=} selected={len(page_data)}"
        )

        return html.Div([
            dmc.AccordionItem(
                value=row["file_id"],
                children=[
                    dmc.AccordionControl(row["file_name"]),
                    dmc.AccordionPanel(
                        html.Div(
                            id={"type": "file-content", "index": row["file_id"]},
                            children=[],
                        )
                    )
                ]
            )
            for _, row in page_data.iterrows()
        ])

    @callback(
        Output({"type": "file-content", "index": MATCH}, "children"),
        State(dataset_id, "value"),
        State(data_store_id, "data"),
        State({"type": "file-content", "index": MATCH}, "id"),
        Input(files_accordion_id, "value"),
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
        Output(filter_store, "data"),
        # State(data_store_id, "data"),
        Input(filter_button_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def filter_file_selection(
        # selected_data: str,
        n_clicks: int,
    ) -> str:
        # selected_data = pd.read_json(StringIO(selected_data), orient="table")
        file_ids = [1] # selected_data["file_id"]
        logger.debug(f"Trigger ID={ctx.triggered_id}: filtering {file_ids=}")
        return file_ids

    return dmc.Col(
        id=sidebar_id,
        span=0,
        style={"display": "none"},
        children=html.Div([
            dmc.Title(
                id=files_count_id,
                order=2
            ),
            dmc.ButtonGroup([
                dmc.Button(
                    id=filter_button_id,
                    variant="light",
                    color="red",
                    children="Filter",
                    n_clicks=0,
                ),
            ]),
            dmc.Pagination(
                id=files_pagination_id,
                size="sm",
                color="indigo",
                total=1,
                page=1,
                siblings=1,
                boundaries=1,
                mt=20,
            ),
            dmc.Accordion(
                id=files_accordion_id,
                value=[],
                chevronPosition="right",
            )
        ]),
    )
