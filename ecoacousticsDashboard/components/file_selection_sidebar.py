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

PAGE_LIMIT = 10

def FileSelectionSidebar(
    dataset_id: str,
    graph_id: str,
    graph_container_id: str,
    sidebar_id: str,
    data_store_id: str,
    span: int = 4,
) -> dmc.Col:
    files_pagination_id = "files-pagination"
    files_count_id = "files-count"
    files_accordion_id = "selection-sidebar-files-accordion"

    @callback(
        Output(graph_container_id, "span"),
        Output(sidebar_id, "span"),
        Output(sidebar_id, "style"),
        Output(data_store_id, "data"),
        Output(files_count_id, "children"),
        Output(files_pagination_id, "page"),
        Output(files_pagination_id, "total"),
        State(dataset_id, "value"),
        Input(graph_id, "selectedData"),
        prevent_initial_call=True,
    )
    def toggle_selection_sidebar(
        dataset_name: str,
        selected_data: Dict[str, Any],
    ) -> Tuple[bool, str, html.Div, str]:
        logger.debug(f"Trigger ID={ctx.triggered_id}: {selected_data=} {dataset_name=}")

        if selected_data is None or len(selected_data['points']) == 0:
            return (
                graph_container_span := 12,
                sidebar_span := 0,
                sidebar_style := {"display": "none"},
                selected_data_json := "",
                selected_text := "",
                current_page := 1,
                total_pages := 1,
            )
        data = dispatch(
            FETCH_FILES,
            dataset_name=dataset_name,
            file_ids=[
                point["hovertext"]
                for point in selected_data["points"]
            ],
        )
        return (
            graph_container_span := 12 - span,
            sidebar_span := span,
            sidebar_style := {"display": "block"},
            selected_data_json := data.to_json(date_format="iso", orient="table"),
            selected_text := f"{len(data)} selected...",
            current_page := 1,
            total_pages := (len(data) + PAGE_LIMIT - 1) // PAGE_LIMIT,
        )

    @callback(
        Output(files_accordion_id, "children"),
        State(data_store_id, "data"),
        Input(files_pagination_id, "page"),
        prevent_initial_call=True,
    )
    def change_page(
        json_data: str,
        current_page: int,
    ) -> html.Div:
        logger.debug(f"Trigger ID={ctx.triggered_id}: {current_page=}")
        data = pd.read_json(StringIO(json_data), orient="table")
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
            for _, row in data.iloc[(current_page - 1):(current_page - 1) + PAGE_LIMIT].iterrows()
        ])

    @callback(
        Output({"type": "file-content", "index": MATCH}, "children"),
        State(data_store_id, "data"),
        State({"type": "file-content", "index": MATCH}, "id"),
        Input(files_accordion_id, "value"),
        prevent_initial_call=True,
    )
    def toggle_file_panel(
        json_data: str,
        matched: str,
        open_values: str,
    ) -> html.Div:
        if (file_id := matched["index"]) not in open_values:
            raise exceptions.PreventUpdate

        data = pd.read_json(StringIO(json_data), orient="table").set_index("file_id")

        file_info = data.loc[file_id]
        return html.Div([
            dcc.Loading(
                dmc.Text(f"{file_id}"),
            )
        ])

    return dmc.Col(
        id=sidebar_id,
        span=0,
        style={"display": "none"},
        children=html.Div([
            dmc.Title(
                id=files_count_id,
                order=2
            ),
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
