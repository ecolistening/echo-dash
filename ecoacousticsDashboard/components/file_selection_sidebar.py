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

def FileSelectionSidebarIcon(
    context: str,
):
    return dmc.HoverCard(
        children=[
            dmc.HoverCardTarget(
                children=dmc.ActionIcon(
                    DashIconify(
                        icon="fluent:multiselect-16-filled",
                        width=24,
                    ),
                    id=f"{context}-toggle-file-sidebar",
                    variant="light",
                    color="blue",
                    size="lg",
                    n_clicks=0,
                ),
            ),
            dmc.HoverCardDropdown(
                children=[
                    dmc.Text("Toggle file selection sidebar"),
                ]
            )
        ],
    )

def FileSelectionSidebar(
    context: str,
    graph: str,
    sibling: str,
    span: int = 4
) -> dmc.GridCol:
    """Render a sidebar for selecting and filtering data points.
    The sidebar is toggled by adjusting the style of itself and its sibling

    Parameters
    ----------
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
        id=f"{context}-file-sidebar",
        span=0,
        style=style_hidden,
        children=html.Div([
            dcc.Store(id=f"{context}-file-sidebar-store"),
            dmc.Stack(
                m="1rem",
                children=[
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Button(
                                "Selected",
                                id=f"{context}-file-sidebar-disclude-button",
                                leftSection=DashIconify(icon="cil:filter"),
                                variant="light",
                                color="red",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Others",
                                id=f"{context}-file-sidebar-include-button",
                                leftSection=DashIconify(icon="cil:filter"),
                                variant="light",
                                color="green",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Undo",
                                id=f"{context}-file-sidebar-undo-button",
                                leftSection=DashIconify(icon="cil:action-undo"),
                                variant="light",
                                color="blue",
                                n_clicks=0,
                            ),
                            dmc.Button(
                                "Reset",
                                id=f"{context}-file-sidebar-reset-button",
                                leftSection=DashIconify(icon="fluent:arrow-reset-20-filled"),
                                variant="light",
                                color="blue",
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
                                    id=f"{context}-file-close-sidebar",
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
                                id=f"{context}-file-sidebar-files-count",
                                size="sm",
                            ),
                        ],
                    ),
                    dmc.Group(
                        grow=True,
                        children=[
                            dmc.Pagination(
                                id=f"{context}-file-sidebar-files-pagination",
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
                                id=f"{context}-file-sidebar-files-accordion",
                                chevronPosition="right",
                                value=[],
                                children="No files selected",
                            ),
                        ],
                    ),
                ],
            ),
        ]),
    )

    @callback(
        Output(sibling, "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "style", allow_duplicate=True),
        State(f"{context}-file-sidebar", "style"),
        Input(f"{context}-file-close-sidebar", "n_clicks"),
        Input(f"{context}-toggle-file-sidebar", "n_clicks"),
        Input("dataset-select", "value"),
        prevent_initial_call=True
    )
    def toggle_selection_sidebar(
        current_style: Dict[str, str],
        close: int,
        n_clicks: int,
        dataset_name: str,
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
        if ctx.triggered_id == "dataset-select" or current_style == style_visible:
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
        Output(f"{context}-file-sidebar", "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "style", allow_duplicate=True),
        Output(f"{context}-file-sidebar-store", "data"),
        Output(f"{context}-file-sidebar-files-count", "children", allow_duplicate=True),
        Output(f"{context}-file-sidebar-files-pagination", "total"),
        Input("dataset-select", "value"),
        State(f"{context}-file-sidebar", "span"),
        State(f"{context}-file-sidebar", "style"),
        Input(graph, "selectedData"),
        Input(graph, "clickData"),
        prevent_initial_call=True,
    )
    def toggle_selection_sidebar(
        dataset_name: str,
        current_span: int,
        current_style: Dict[str, str],
        lassoo_data: Dict[str, Any],
        clicked_data: Dict[str, Any],
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
        selected_data = lassoo_data or clicked_data
        if ctx.triggered_id == "dataset-select" or selected_data is None or len((points := selected_data['points'])) == 0:
            return (
                sibling_span := 12 - current_span,
                sidebar_span := current_span,
                sidebar_style := current_style,
                selected_data_json := "",
                selected_text := "",
                total_pages := 1,
            )
        data = dispatch(FETCH_FILES, dataset_name=dataset_name)
        data = data.loc[data["file_id"].isin([point["hovertext"] for point in points]), ["file_id", "file_path"]]
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
        Output(f"{context}-file-sidebar-files-accordion", "children"),
        Output(f"{context}-file-sidebar-files-count", "children", allow_duplicate=True),
        State(f"{context}-file-sidebar-store", "data"),
        Input(f"{context}-file-sidebar-files-pagination", "value"),
        Input(f"{context}-file-sidebar-files-pagination", "total"),
        prevent_initial_call=True,
    )
    def change_page(
        selected_json_data: str,
        current_page: int,
        total_pages: int,
    ) -> dmc.Box:
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
        if selected_json_data == "" or selected_json_data is None:
            return (
                accordion_items := "No files selected",
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
                value=row["file_path"],
                children=[
                    dmc.AccordionControl(row["file_path"].split("/")[-1]),
                    dmc.AccordionPanel(
                        dmc.Box(
                            id={"type": f"{context}-file-sidebar-file-data", "index": row["file_path"]},
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
        Output({"type": f"{context}-file-sidebar-file-data", "index": MATCH}, "children"),
        State("dataset-select", "value"),
        State(f"{context}-file-sidebar-store", "data"),
        State({"type": f"{context}-file-sidebar-file-data", "index": MATCH}, "id"),
        Input(f"{context}-file-sidebar-files-accordion", "value"),
        prevent_initial_call=True,
    )
    def toggle_file_panel(
        dataset_name: str,
        selected_json_data: str,
        matched: str,
        open_values: str,
    ) -> dmc.Box:
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
        if (file_path := matched["index"]) not in open_values:
            raise exceptions.PreventUpdate
        config = dispatch(FETCH_DATASET_CONFIG, dataset_name=dataset_name)
        audio_bytes, mime_type, _ = AudioAPI.get_audio_bytes(file_path, dataset_name, config)
        if audio_bytes is not None:
            return dmc.Box([
                dcc.Loading(
                    html.Audio(
                        id="audio-player",
                        src=audio_bytes_to_enc(audio_bytes, mime_type),
                        controls=True,
                    ),
                )
            ])
        else:
            return dmc.Box([
                dmc.Text("Audio not available on server")
            ])

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Output(sibling, "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "style", allow_duplicate=True),
        Input(f"{context}-file-sidebar-include-button", "n_clicks"),
        State("dataset-select", "value"),
        State(f"{context}-file-sidebar-store", "data"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def include_file_selection(
        n_clicks: int,
        dataset_name: str,
        selected_json_data: str,
        filters: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        """Add *all other* file_ids to the filter store

        Parameters
        ----------
        selected_json_data: str
            The file data as JSON parsable as a table using pandas
        filtered_file_ids: list
            A list of unique file ids currently discluded from the graph

        Returns
        -------
        "filter-store": list
            An updated list of unique file ids to disclude from the graph
        """
        if not n_clicks: return no_update
        selected_file_ids = pd.read_json(StringIO(selected_json_data), orient="table")["file_id"]
        data = dispatch(FETCH_FILES, dataset_name=dataset_name)
        file_ids = set(data.loc[~data["file_id"].isin(selected_file_ids), "file_id"].tolist())
        file_filter = filters["files"]
        selection_id = len(file_filter.keys()) + 1
        file_filter[selection_id] = list(file_ids)
        filters["files"] = file_filter
        return filters, 12, 0, style_hidden

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Output(sibling, "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "style", allow_duplicate=True),
        Input(f"{context}-file-sidebar-disclude-button", "n_clicks"),
        State(f"{context}-file-sidebar-store", "data"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def disclude_file_selection(
        n_clicks: int,
        selected_json_data: str,
        filters: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        """Add *selected* file_ids to the filter store

        Parameters
        ----------
        selected_json_data: str
            The file data as JSON parsable as a table using pandas
        filters: dict

        Returns
        -------
        filters: dict
        """
        if not n_clicks: return no_update
        file_ids = set(pd.read_json(StringIO(selected_json_data), orient="table")["file_id"].tolist())
        file_filter = filters["files"]
        selection_id = len(file_filter.keys()) + 1
        file_filter[selection_id] = list(file_ids)
        filters["files"] = file_filter
        return filters, 12, 0, style_hidden

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Output(sibling, "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "style", allow_duplicate=True),
        Input(f"{context}-file-sidebar-undo-button", "n_clicks"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def undo_last_file_selection(
        n_clicks: int,
        filters: Dict[str, Any],
    ) -> str:
        """Remove the last file filter

        Returns
        -------
        filters: dict
        """
        if not n_clicks:
            return no_update
        file_filters = filters["files"]
        if not len(file_filters):
            return no_update
        selection_ids = list(map(int, file_filters.keys()))
        file_filters.pop(str(max(selection_ids)), None)
        filters["files"] = file_filters
        if not len(file_filters):
            return filters, 12, 0, style_hidden
        return filters, no_update, no_update, no_update

    @callback(
        Output("filter-store", "data", allow_duplicate=True),
        Output(sibling, "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "span", allow_duplicate=True),
        Output(f"{context}-file-sidebar", "style", allow_duplicate=True),
        Input(f"{context}-file-sidebar-reset-button", "n_clicks"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    def reset_file_selection(
        n_clicks: int,
        filters: Dict[str, Any],
    ) -> str:
        """Reset the scope of the file filters, reverting back to the original graph data

        Returns
        -------
        filters: dict
        """
        if not n_clicks or not len(filters["files"]):
            return no_update
        filters["files"] = {}
        return filters, 12, 0, style_hidden

    return component
