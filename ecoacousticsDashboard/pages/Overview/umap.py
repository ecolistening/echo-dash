import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import dcc
from dash_iconify import DashIconify

from callbacks.filter import date_filter_callbacks
from callbacks.filter import file_filter_callbacks
from callbacks.filter import site_level_filter_callbacks
from callbacks.pages import umap_callbacks

from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.file_selection_sidebar import FileSelectionSidebar
from components.figure_download_widget import FigureDownloadWidget

PAGE_NAME = "UMAP"
PAGE_TITLE = "UMAP of Soundscape Descriptors"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=PAGE_NAME,
)

def FileSelectionSidebarIcon():
    return dmc.HoverCard(
        children=[
            dmc.HoverCardTarget(
                children=dmc.ActionIcon(
                    DashIconify(
                        icon="fluent:multiselect-16-filled",
                        width=24,
                    ),
                    id="toggle-file-sidebar",
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

layout = dmc.Box([
    dcc.Store(id="umap-graph-data"),
    dcc.Store(id="umap-category-orders"),
    FilterPanel([
        dmc.Group(
            align="start",
            grow=True,
            children=[
                SiteLevelFilter(),
                DateRangeFilter(),
                EnvironmentalFilter(),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="umap-colour-select",
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="umap-symbol-select",
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="umap-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="umap-facet-column-select",
                    label="Facet columns by"
                ),
                dmc.Flex(
                    p="1rem",
                    align="center",
                    justify="right",
                    direction="row",
                    children=[
                        dmc.Group(
                            grow=True,
                            children=[
                                FileSelectionSidebarIcon(),
                                DataDownloadWidget(
                                    graph_data="umap-graph-data",
                                ),
                                FigureDownloadWidget(
                                    plot_name="umap-graph",
                                ),
                            ]
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            grow=True,
            children=[
                dmc.Stack([
                    dmc.Text(
                        "Dot Size",
                        size="sm",
                        ta="left",
                    ),
                    dmc.Slider(
                        id="umap-size-slider",
                        min=1,
                        max=20,
                        step=1,
                        value=6,
                        marks=[
                            {"value": i, "label": f"{i}"}
                            for i in (1, 10, 20)
                        ],
                        persistence=True
                    )
                ]),
                dmc.Stack([
                    dmc.Text(
                        "Opacity",
                        size='sm',
                        ta="left",
                    ),
                    dmc.Slider(
                        id="umap-opacity-slider",
                        persistence=True,
                        min=0,
                        max=100,
                        step=5,
                        value=50,
                        marks=[
                            dict(value=i, label=f"{i}%")
                            for i in range(0, 101, 20)
                        ],
                    )
                ]),
                dmc.Stack([
                    dmc.Text(
                        "Sample Size",
                        size="sm",
                        ta="left",
                    ),
                    dmc.Slider(
                        id=f"umap-sample-slider",
                        persistence=True,
                        min=1,
                        value=None,
                        step=1,
                    )
                ]),
            ]
        ),
    ]),
    # Note: this is slightly hacky but it works
    # the file selection sidebar changes the span of the
    # sibling column span to make itself visible
    # A better solution to get the loading component
    # to work properly would be to render the whole Graph
    # element with the callback, however this causes
    # some cascade effects, so parking for now
    dmc.Grid([
        dmc.GridCol(
            id="umap-graph-container",
            span=12,
            children=[
                dcc.Loading([
                    dcc.Graph(id="umap-graph"),
                ]),
            ],
        ),
        FileSelectionSidebar(
            graph_data="umap-graph-data",
            filter_data="umap-filter-store",
            graph="umap-graph",
            sibling="umap-graph-container",
            span=5,
        ),
    ]),
    dbc.Offcanvas(
        id="umap-page-info",
        is_open=False,
        placement="bottom",
        children=dmc.Grid(
            children=[
                dmc.GridCol(
                    span=4,
                    children=[
                        dmc.Title(PAGE_TITLE, order=2),
                    ],
                ),
                dmc.Divider(
                    variant="dotted",
                    orientation="vertical"
                ),
                dmc.GridCol(
                    span="auto",
                    children=[
                        dmc.Text(
                            "UMAP is a method of projecting high-dimensional data onto fewer dimensions. "
                            "The axes themselves have no precise meaning, other than defining the distance "
                            "between the data points. ",
                            span=True,
                        ),
                        dmc.Anchor(
                            '[details]',
                            href='https://pair-code.github.io/understanding-umap/',
                            target="_blank", # target="_blank" opens link in a new tab
                        ),
                    ]
                ),
            ]
        ),
    ),
])
