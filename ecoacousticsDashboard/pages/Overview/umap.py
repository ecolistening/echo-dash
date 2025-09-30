import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

from dash import dcc
from dash_iconify import DashIconify

from api import FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.file_selection_sidebar import FileSelectionSidebar, FileSelectionSidebarIcon
from components.figure_download_widget import FigureDownloadWidget
from utils.content import get_content

PAGE_NAME = "UMAP"
PAGE_TITLE = "UMAP of Soundscape Descriptors"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name=PAGE_NAME,
)

layout = dmc.Box([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="umap-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="umap-symbol-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="umap-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="umap-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
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
                                FileSelectionSidebarIcon(context="umap"),
                                DataDownloadWidget(
                                    context="umap",
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
                        value=33,
                        marks=[
                            dict(value=i, label=f"{i}%")
                            for i in range(0, 101, 20)
                        ],
                    )
                ]),
                # dmc.Stack([
                #     dmc.Text(
                #         "Sample Size",
                #         size="sm",
                #         ta="left",
                #     ),
                #     dmc.Slider(
                #         id=f"umap-sample-slider",
                #         persistence=True,
                #         min=1,
                #         value=None,
                #         step=1,
                #     )
                # ]),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
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
            context="umap",
            graph="umap-graph",
            sibling="umap-graph-container",
            span=5,
        ),
    ]),
    dmc.Box(
        id="soundade-features-description",
        children=[]
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/umap")
    ),
])

def register_callbacks():
    from callbacks.pages import umap_callbacks
    umap_callbacks.register_callbacks()
