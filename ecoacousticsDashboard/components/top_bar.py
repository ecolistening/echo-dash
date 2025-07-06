import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd

from dash import html, ctx, dcc, callback
from dash import Output, Input, State
from dash_iconify import DashIconify
from io import StringIO
from loguru import logger
from typing import Any, Callable, Dict, List, Tuple

from components.figure_downloader import FigureDownloader

def TopBar(
    dataset_id: str,
    graph_id: str,
    plot_data_id: str | None = None,
    children: List[html.Div] = [],
) -> html.Div:
    download_dataframe_id = "download-dataframe"

    if plot_data_id:
        @callback(
            Output(download_dataframe_id, "data"),
            State(dataset_id, "value"),
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
            *args: Any,
            **kwargs: Any,
        ) -> Dict[str, Any]:
            logger.debug(
                f"Trigger ID={ctx.triggered_id}:"
                f"dataset={dataset_name} json data ({len(json_data)}B)"
            )
            dl_type = ctx.triggered_id
            data = pd.read_json(StringIO(json_data), orient='table')
            data_type = dl_type.split("_")[-1]
            if data_type == "csv":
                data_to_format = data.to_csv
            elif data_type == "xls":
                data_to_format = data.to_excel
            elif data_type == "json":
                data_to_format = data.to_json
            elif data_type == "parquet":
                data_to_format = data.to_parquet
            else:
                return ""
            return dcc.send_data_frame(data_to_format, f'{dataset_name}.{data_type}')

    return html.Div([
        html.Div() if not plot_data_id else dcc.Download(id=download_dataframe_id),
        dmc.Group(
            grow=True,
            style={"margin-bottom": "0.5em"},
            children=[
                *children,
                html.Div(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=dmc.Group(
                        grow=True,
                        children=[
                            dmc.HoverCard(
                                children=[
                                    dmc.HoverCardTarget(
                                        children=dmc.ActionIcon(
                                            DashIconify(
                                                icon="uil:filter",
                                                width=24,
                                            ),
                                            id="toggle-filter-menu",
                                            variant="light",
                                            color="blue",
                                            size="lg",
                                            n_clicks=0,
                                        ),
                                    ),
                                    dmc.HoverCardDropdown(
                                        children=[
                                            dmc.Text("View filters"),
                                        ]
                                    )
                                ],
                            ),
                            dmc.HoverCard(
                                children=[
                                    dmc.HoverCardTarget(
                                        children=dmc.ActionIcon(
                                            DashIconify(
                                                icon="uil:image-download",
                                                width=24,
                                            ),
                                            id="image-download-icon",
                                            variant="light",
                                            color="blue",
                                            size="lg",
                                            n_clicks=0,
                                        ),
                                    ),
                                    dmc.HoverCardDropdown(
                                        children=[
                                            dmc.Text("Download image as..."),
                                            FigureDownloader(graph_id),
                                        ]
                                    )
                                ],
                            ),
                            dmc.HoverCard(
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
                                            dmc.Text("Export filtered data as..."),
                                            dmc.Group(
                                                grow=True,
                                                children=[
                                                    dmc.Button("csv", variant="filled", id='dl_csv'),
                                                    dmc.Button("excel", variant="filled", id='dl_xls'),
                                                    dmc.Button("json", variant="filled", id='dl_json'),
                                                    dmc.Button("parquet", variant="filled", id='dl_parquet'),
                                                ],
                                            )
                                        ]
                                    )
                                ],
                            ),
                            dmc.HoverCard(
                                children=[
                                    dmc.HoverCardTarget(
                                        children=dmc.ActionIcon(
                                            DashIconify(
                                                icon="uil:info-circle",
                                                width=24,
                                            ),
                                            id="info-icon",
                                            variant="light",
                                            color="blue",
                                            size="lg",
                                            n_clicks=0,
                                        ),
                                    ),
                                    dmc.HoverCardDropdown(
                                        dmc.Text("View page information"),
                                    )
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ])
