import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd

from dash import callback, ctx, dcc, no_update, clientside_callback
from dash import Input, State, Output
from dash_iconify import DashIconify
from loguru import logger
from io import StringIO

from typing import Any, Callable, Dict, List, Tuple

def register_download_callbacks(
    trigger_id: str,
    source_id: str,
    sink_id: str,
    extension: str,
    render: Callable,
    params: Dict[str, Any],
) -> None:
    clientside_callback(
        """
        function updateLoadingState(n_clicks) {
            return true
        }
        """,
        Output(trigger_id, "loading", allow_duplicate=True),
        Input(trigger_id, "n_clicks"),
        prevent_initial_call=True,
    )

    @callback(
        Output(sink_id, "data", allow_duplicate=True),
        Output(trigger_id, "loading"),
        State("dataset-select", "value"),
        State(source_id, "data"),
        Input(trigger_id, "n_clicks"),
        prevent_initial_call=True,
    )
    def send_download(
        dataset_name,
        json_data: str,
        n_clicks: int,
    ) -> Tuple[Any, bool]:
        if json_data is None or not len(json_data): return no_update
        triggered_id = ctx.triggered_id
        action = "EXPORT_DATA"
        file_name = f"{dataset_name}.{extension}"
        data = pd.read_json(StringIO(json_data), orient="table")
        logger.debug(f"{triggered_id=} {action=} {file_name=} {params=} rows={len(data)}")
        return dcc.send_data_frame(render(data), file_name, **params), False

def DataDownloadWidget(
    graph_data: str,
) -> dmc.HoverCard:
    """Render a hover card with a download icon

    Parameters
    ----------
    graph_data: str
        The element ID for a dcc.Store containing json graph data

    Returns
    -------
    dmc.HoverCard
    """
    download_params = {
        "csv": {"trigger_id": "dl_csv", "extension": "csv", "render": lambda df: df.to_csv, "params": {} },
        "excel": {"trigger_id": "dl_excel", "extension": "xlsx", "render": lambda df: df.to_excel, "params": { "sheet_name": "Sheet 1" } },
        "json": {"trigger_id": "dl_json", "extension": "json", "render": lambda df: df.to_json, "params": {} },
        "parquet": {"trigger_id": "dl_parquet", "extension": "parquet", "render": lambda df: df.to_parquet, "params": {} },
    }

    buttons = []
    for dl_type, dl_params in download_params.items():
        buttons.append(dmc.Button(
            id=dl_params["trigger_id"],
            children=dl_type,
            variant="filled",
        ))
        register_download_callbacks(source_id=graph_data, sink_id="data-download", **dl_params)

    return dmc.HoverCard(
        children=[
            dmc.HoverCardTarget(
                children=dmc.ActionIcon(
                    DashIconify(
                        icon="uil:file-download-alt",
                        width=24,
                    ),
                    id="export-data-icon",
                    variant="light",
                    color="blue",
                    size="lg",
                    n_clicks=0,
                ),
            ),
            dmc.HoverCardDropdown(
                children=[
                    dcc.Download(id="data-download"),
                    dmc.Text("Export filtered data as..."),
                    dmc.Group(
                        grow=True,
                        children=buttons,
                    )
                ]
            )
        ],
    )
