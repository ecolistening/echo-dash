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
    graph_data: str,
    filter_data: str,
    graph: str,
    sibling: str,
    span: int = 4
) -> dmc.GridCol:
    """Render a sidebar for selecting and filtering data points.
    The sidebar is toggled by adjusting the style of itself and its sibling

    Parameters
    ----------
    graph_data: str
        The element ID for a dcc.Store containing json graph data
    filter_data: str
        The element ID for a dcc.Store containing a discluded list of file IDs
    graph: str
        The element ID for a dcc.Graph
    sibling: str
        The element ID for a sibling dmc.GridCol containing the graph

    Returns
    -------
    dmc.GridCol
        The sidebar container, initialized as hidden
    """
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
                                "Filter selected",
                                id="file-sidebar-disclude-button",
                                leftSection=DashIconify(icon="f7:delete-left-fill"),
                                variant="light",
                                color="red",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Filter remaining",
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
        Output(sibling, "span", allow_duplicate=True),
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
        """Toggle the sidebar

        Parameters
        ----------
        current_style: int
            The current style of the sidebar
        close: int
            Input from the close element (not used for governing state)
        n_clicks: int
            Input from the toggle element (not used for governing state)

        Returns
        -------
        sibling_span: int
            Updated span of the sibling element
        sidebar_span: int
            Updated span of the sidebar element
        sidebar_style: dict
            Updated styling of the sidebar element (resetting display)
        """
        if current_style == style_visible:
            return (
                sibling_span := 12,
                sidebar_span := 0,
                sidebar_style := style_hidden,
            )
        return (
            sibling_span := 12 - span,
            sidebar_span := span,
            sidebar_style := style_visible,
        )

    @callback(
        Output(sibling, "span", allow_duplicate=True),
        Output("file-sidebar", "span", allow_duplicate=True),
        Output("file-sidebar", "style", allow_duplicate=True),
        Output("file-sidebar-store", "data"),
        Output("file-sidebar-files-count", "children", allow_duplicate=True),
        Output("file-sidebar-files-pagination", "total"),
        State("dataset-select", "value"),
        State("file-sidebar", "span"),
        State("file-sidebar", "style"),
        Input(graph, "selectedData"),
        prevent_initial_call=True,
    )
    def toggle_selection_sidebar(
        dataset_name: str,
        current_span: int,
        current_style: Dict[str, str],
        selected_data: Dict[str, Any],
    ) -> Tuple[int, int, Dict[str, str], str, str, int]:
        """Toggle the sidebar and populate the selected data store

        Parameters
        ----------
        dataset_name: str
            The name of the currently selected dataset
        current_span: int
            The current span of the sidebar
        current_style: int
            The current style of the sidebar
        selected_data: dict
            The data as returned by the 'selectedData' hook on a plotly graph object

        Returns
        -------
        sibling_span: int
            Updated span of the sibling element
        sidebar_span: int
            Updated span of the sidebar element
        sidebar_style: dict
            Updated styling of the sidebar element (resetting display)
        selected_data_json: str
            The data for selected data points encoded as a json string
        selected_text: str
            Pagination text describing which page we are on
        total_pages: int
            The total number of pages for pagination
        """
        if selected_data is None or len((points := selected_data['points'])) == 0:
            return (
                sibling_span := 12 - current_span,
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
            sibling_span := 12 - span,
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
        selected_json_data: str,
        current_page: int,
        total_pages: int,
    ) -> html.Div:
        """Populate the current page with an accordion for each file

        Parameters
        ----------
        selected_json_data: str
            The file data as JSON parsable as a table using pandas
        current_page: int
            The selected page number
        open_values: str
            The total number of pages

        Returns
        -------
        children: list
            A list of dmc.AccordionItems for each file_id
        """
        if json_data == "" or json_data is None:
            return (
                accordion_items := [],
                selected_text := "",
            )

        data = pd.read_json(StringIO(selected_json_data), orient="table")
        page_data = data.iloc[(current_page - 1):(current_page - 1) + PAGE_LIMIT]

        logger.debug(
            f"Trigger ID={ctx.triggered_id}: "
            f"{current_page=} selected={len(page_data)}"
        )

        accordion_items = [
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
        ]

        total = len(data)
        start = PAGE_LIMIT * (current_page - 1) + 1
        end = min(total, PAGE_LIMIT * current_page)
        selected_text = f"Showing {start} - {end} / {total}",

        return accordion_items, selected_text

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
        selected_json_data: str,
        matched: str,
        open_values: str,
    ) -> html.Div:
        """Toggle the accordion panel for a single file,
        showing file metadata and a html audio element

        Parameters
        ----------
        dataset_name: str
            The name of the currently selected dataset
        selected_json_data: str
            The file data as JSON parsable as a table using pandas
        matched: str
            The pattern matcher for the selected file, where 'index' is a file_id
        open_values: str
            The list of file_ids present on the current page

        Returns
        -------
        component: dmc.Box
            A html element containing file metadata and audio
        """
        if (file_id := matched["index"]) not in open_values:
            raise exceptions.PreventUpdate

        config = dispatch(FETCH_DATASET_CONFIG, dataset_name=dataset_name)
        data = pd.read_json(StringIO(selected_json_data), orient="table").set_index("file_id")

        file_info = data.loc[file_id]
        audio_bytes, mime_type, _ = AudioAPI.get_audio_bytes(file_info.file_path, dataset_name, config)
        return dmc.Box([
            dcc.Loading(
                html.Audio(
                    id="audio-player",
                    src=audio_bytes_to_enc(audio_bytes, mime_type),
                    controls=True
                ),
            )
        ])

    @callback(
        Output(filter_data, "data", allow_duplicate=True),
        State(graph_data, "data"),
        State("file-sidebar-store", "data"),
        State(filter_data, "data"),
        Input("file-sidebar-include-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def include_file_selection(
        graph_json_data: str,
        selected_json_data: str,
        filtered_file_ids: Dict[str, Any],
        n_clicks: int,
    ) -> str:
        """Add *all other* file_ids to the filter store

        Parameters
        ----------
        graph_json_data: str
            The graph data as JSON parsable as a table using pandas
        selected_json_data: str
            The file data as JSON parsable as a table using pandas
        filtered_file_ids: list
            A list of unique file ids currently discluded from the graph

        Returns
        -------
        filter_data: list
            An updated list of unique file ids to disclude from the graph
        """
        if not n_clicks: return no_update
        filtered_file_ids = set(filtered_file_ids or [])
        selected_file_ids = pd.read_json(StringIO(selected_json_data), orient="table")["file_id"]
        graph_data = pd.read_json(StringIO(graph_json_data), orient="table")
        file_ids = set(graph_data.loc[~graph_data["file_id"].isin(selected_file_ids), "file_id"].tolist())
        return list(filtered_file_ids.union(file_ids))

    @callback(
        Output(filter_data, "data", allow_duplicate=True),
        State("file-sidebar-store", "data"),
        State(filter_data, "data"),
        Input("file-sidebar-disclude-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def disclude_file_selection(
        selected_json_data: str,
        filtered_file_ids: Dict[str, Any],
        n_clicks: int,
    ) -> List[str]:
        """Add *selected* file_ids to the filter store

        Parameters
        ----------
        selected_json_data: str
            The file data as JSON parsable as a table using pandas
        filtered_file_ids: list
            A list of unique file ids currently discluded from the graph

        Returns
        -------
        filter_data: list
            An updated list of unique file ids to disclude from the graph
        """
        if not n_clicks: return no_update
        filtered_file_ids = set(filtered_file_ids or [])
        file_ids = set(pd.read_json(StringIO(selected_json_data), orient="table")["file_id"].tolist())
        return list(filtered_file_ids.union(file_ids))

    @callback(
        Output(filter_data, "data", allow_duplicate=True),
        State(filter_data, "data"),
        Input("file-sidebar-reset-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_file_selection(
        filtered_file_ids: Dict[str, Any],
        n_clicks: int,
    ) -> str:
        """
        Reset the scope of the file filters, reverting back to the original graph data

        Parameters
        ----------
        filtered_file_ids: list
            A list of unique file ids currently discluded from the graph

        Returns
        -------
        filter_data: list
            An empty list
        """
        if not n_clicks: return no_update
        return []

    return component
