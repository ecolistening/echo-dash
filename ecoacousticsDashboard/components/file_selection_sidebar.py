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

def FileSelectionSidebar(
    dataset_id: str,
    graph_id: str,
    sidebar_id: str,
    data_store_id: str,
) -> dbc.Offcanvas:
    files_count_id = "files_count"
    files_accordion_id = "selection-sidebar-files-accordion"
    files_panel = [
        dmc.AccordionItem(
            value="files",
            children=[
                dmc.AccordionControl("Files"),
                dmc.AccordionPanel(
                    dmc.Accordion(
                        id=files_accordion_id,
                        value=[],
                        chevronPosition="right",
                    )
                )
            ]
        )
    ]
    sidebar = dbc.Offcanvas(
        id=sidebar_id,
        children=html.Div([
            dmc.Title(
                id=files_count_id,
                order=2
            ),
            dmc.Accordion(
                chevronPosition="right",
                children=files_panel,
            ),
        ]),
        is_open=False,
        placement="end",
        backdrop=False,
    )

    @callback(
        Output(sidebar_id, "is_open"),
        Output(data_store_id, "data"),
        Output(files_accordion_id, "children"),
        Output(files_count_id, "children"),
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
            return False, "", html.Div(), f"None selected..."

        file_ids = [point["hovertext"] for point in selected_data["points"]]
        data = dispatch(
            FETCH_FILES,
            dataset_name=dataset_name,
            file_ids=file_ids,
        )
        files_accordion = html.Div([
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
            for _, row in data.iterrows()
        ])
        json_data = data.to_json(
            date_format="iso",
            orient="table",
        )
        return True, json_data, files_accordion, f"{len(data)} selected..."

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

        data = pd.read_json(
            StringIO(json_data),
            orient="table"
        ).set_index("file_id")

        file_info = data.loc[file_id]
        return html.Div([
            dcc.Loading(
                dmc.Text(f"{file_id}"),
            )
        ])

    return sidebar
