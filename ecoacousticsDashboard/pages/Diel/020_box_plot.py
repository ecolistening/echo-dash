import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import dcc
from dash_iconify import DashIconify

from api import FETCH_DATASET_DROPDOWN_OPTION_GROUPS
from callbacks.pages import index_box_callbacks
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

PAGE_NAME = "index-box-plot"
PAGE_TITLE = "Box Plot of Acoustic Descriptor by Time of Day"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Box Plot"
)

PLOT_HEIGHT = 800

layout = dmc.Box([
    FilterPanel([
        dmc.Stack(
            children=[
                SiteLevelFilter(),
                dmc.Divider(variant="solid"),
                DateRangeFilter(),
                dmc.Divider(variant="solid"),
                EnvironmentalFilter(),
            ]
        )
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                dmc.Select(
                    id="feature-select",
                    label="Acoustic Feature",
                    value="bioacoustic index",
                    searchable=True,
                    clearable=False,
                    allowDeselect=False,
                ),
                DatasetOptionsSelect(
                    id="index-box-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="index-box-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by",
                ),
                DatasetOptionsSelect(
                    id="index-box-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet columns by",
                    value="year",
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
                                FileSelectionSidebarIcon(context="index-box"),
                                DataDownloadWidget(
                                    context="index-box",
                                ),
                                FigureDownloadWidget(
                                    plot_name="index-box-graph",
                                ),
                            ],
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
                        "Acoustic Feature Range",
                        id="feature-range-title",
                        size="sm",
                        ta="left",
                    ),
                    dmc.RangeSlider(
                        id="feature-range-slider",
                        min=0,
                        max=999,
                        step=1,
                        persistence=True,
                        showLabelOnHover=False,
                    ),
                ]),
                dmc.Stack([
                    dmc.Text(
                        "Time Aggregation",
                        size="sm",
                        ta="left",
                    ),
                    dmc.SegmentedControl(
                        id="index-box-time-aggregation",
                        data=[
                            {"value": "time", "label": "15 minutes"},
                            {"value": "hour", "label": "1 hour"},
                            {"value": "dddn", "label": "Dawn-Day-Dusk-Night"}
                        ],
                        value="dddn",
                        persistence=True
                    ),
                ]),
                dmc.Stack([
                    dmc.Chip(
                        "Outliers",
                        id="index-box-outliers-tickbox",
                        value="outlier",
                        checked=True,
                        persistence=True,
                    ),
                ]),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dmc.Grid([
        dmc.GridCol(
            id="index-box-graph-container",
            span=12,
            children=[
                dcc.Loading([
                    dcc.Graph(id="index-box-graph"),
                ]),
            ],
        ),
        FileSelectionSidebar(
            context="index-box",
            graph="index-box-graph",
            sibling="index-box-graph-container",
            span=5,
        ),
    ]),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/acoustic-feature-box")
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="feature-descriptor-content",
        children=[],
    ),
])

def register_callbacks():
    from callbacks.pages import index_box_callbacks
    index_box_callbacks.register_callbacks()
