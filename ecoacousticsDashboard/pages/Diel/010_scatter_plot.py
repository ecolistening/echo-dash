import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

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
from components.acoustic_feature_filter import AcousticFeatureFilter
from components.figure_download_widget import FigureDownloadWidget
from components.file_selection_sidebar import FileSelectionSidebar, FileSelectionSidebarIcon
from components.footer import Footer

PAGE_NAME = 'index-scatter'
PAGE_TITLE = 'Acoustic Descriptor by Time of Day'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Scatter Plot'
)

PLOT_HEIGHT = 800

layout = dmc.Box([
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
        dmc.Space(h=10),
        dmc.Group(
            align="start",
            grow=True,
            children=[
                AcousticFeatureFilter(),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="index-scatter-x-axis-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Time",),
                    label="X-axis",
                    value="time",
                ),
                DatasetOptionsSelect(
                    id="index-scatter-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="index-scatter-symbol-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="index-scatter-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by",
                ),
                DatasetOptionsSelect(
                    id="index-scatter-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet columns by",
                    value="month",
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
                                FileSelectionSidebarIcon(context="index-scatter"),
                                DataDownloadWidget(
                                    context="index-scatter",
                                ),
                                FigureDownloadWidget(
                                    plot_name="index-scatter-graph",
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
                        "Dot Size",
                        size="sm",
                        ta="left",
                    ),
                    dmc.Slider(
                        id="index-scatter-size-slider",
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
                        id="index-scatter-opacity-slider",
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
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dmc.Grid([
        dmc.GridCol(
            id="index-scatter-graph-container",
            span=12,
            children=[
                dcc.Loading([
                    dcc.Graph(id="index-scatter-graph"),
                ]),
            ],
        ),
        FileSelectionSidebar(
            context="index-scatter",
            graph="index-scatter-graph",
            sibling="index-scatter-graph-container",
            span=5,
        ),
    ]),
    # dcc.Loading(
    #     dcc.Graph(id=f"index-scatter-graph"),
    # ),
    dbc.Offcanvas(
        id="index-scatter-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-scatter"),
    ),
])

def register_callbacks():
    from callbacks.pages import index_scatter_callbacks
    index_scatter_callbacks.register_callbacks()
