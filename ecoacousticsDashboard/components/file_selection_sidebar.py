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
) -> dmc.GridCol:
    """
    Listen to the 'selectedData' callback on the plot and toggle a sidebar to appear alongside a graph.
    Displays:

    - Buttons to filter the data by include / disclude filtering. For more details on how this works, see FILTER.md
    - A paginated list of samples (i.e. files) displayed in an accordion.
    - Each accordion item panel contains the ability to playback the audio file
    """
    files_pagination_id = "selection-sidebar-files-pagination"
    files_count_id = "selection-sidebar-files-count"
    files_accordion_id = "selection-sidebar-files-accordion"
    file_data_id = "selection-sidebar-file-data"
    filter_include_button_id = "selection-sidebar-filter-include-button"
    filter_disclude_button_id = "selection-sidebar-filter-disclude-button"

    style_hidden = dict(display="none")
    style_visible = dict(display="block")

    @callback(
        Output(graph_container_id, "span"),
        Output(sidebar_id, "span"),
        Output(sidebar_id, "style"),
        Output(data_store_id, "data"),
        Output(files_count_id, "children", allow_duplicate=True),
        Output(files_pagination_id, "total"),
        State(dataset_id, "value"),
        Input(graph_id, "selectedData"),
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
        Output(files_accordion_id, "children"),
        Output(files_count_id, "children", allow_duplicate=True),
        State(data_store_id, "data"),
        Input(files_pagination_id, "value"),
        Input(files_pagination_id, "total"),
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
                            id={"type": file_data_id, "index": row["file_id"]},
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
        Output({"type": file_data_id, "index": MATCH}, "children"),
        State(dataset_id, "value"),
        State(data_store_id, "data"),
        State({"type": file_data_id, "index": MATCH}, "id"),
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
        Output(filter_include_button_id, "n_clicks"),
        Input(filter_include_button_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def include_file_selection(
        n_clicks: int,
    ) -> str:
        # TODO: include filter means adding all other file_ids to the store
        logger.debug("clicked", n_clicks)
        return n_clicks

    @callback(
        Output(filter_disclude_button_id, "n_clicks"),
        Input(filter_disclude_button_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def disclude_file_selection(
        n_clicks: int,
    ) -> str:
        # TODO: disclude filter means adding these file_ids to the store
        logger.debug("clicked", n_clicks)
        return n_clicks

    return dmc.GridCol(
        id=sidebar_id,
        span=0,
        style=style_hidden,
        children=dmc.Stack(
            style={"margin-top": "1rem"},
            children=[
                dmc.Group(
                    grow=True,
                    children=[
                        dmc.Button(
                            "Filter Selected",
                            id=filter_disclude_button_id,
                            variant="light",
                            color="red",
                            n_clicks=0,
                        ),
                        dmc.Button(
                            "Filter Remaining",
                            id=filter_include_button_id,
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
                            id=files_count_id,
                            size="sm",
                        ),
                    ],
                ),
                dmc.Group(
                    grow=True,
                    children=[
                        dmc.Pagination(
                            id=files_pagination_id,
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
                            id=files_accordion_id,
                            chevronPosition="right",
                            value=[],
                            children=[],
                        ),
                    ],
                ),
            ],
        ),
    )
