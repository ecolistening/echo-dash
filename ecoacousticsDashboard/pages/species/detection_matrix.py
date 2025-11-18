import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np

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
from components.figure_download_widget import FigureDownloadWidget
from utils.content import get_content
from utils.sketch import empty_figure

dash.register_page(
    __name__,
    title="Species Detection Matrix",
    name="Detection Matrix",
    path="/species/detection-matrix",
    order=1,
)

layout = dmc.Box([
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="species-community-axis-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level", "Time of Day", "Temporal"), # "Spatial"),
                    label="Column facet 1 by...",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="species-community-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level", "Time of Day", "Temporal"), # "Spatial"),
                    label="Column facet 2 by...",
                    value="dddn",
                ),
                DatasetOptionsSelect(
                    id="species-matrix-filter",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Functional Groups", "Species Habitat"),
                    label="Paginate by...",
                ),
                dmc.Chip(
                    "Only Species List",
                    id="species-list-tickbox",
                    checked=False,
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
                                DataDownloadWidget(
                                    context="species-community",
                                ),
                                FigureDownloadWidget(
                                    plot_name="species-community-graph",
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
                        children="Detection Threshold",
                        size="sm",
                        ta="right",
                    ),
                    dmc.Slider(
                        id="species-threshold-slider",
                        min=0.0, max=0.99,
                        step=0.1, value=0.5,
                        persistence=True,
                        marks=[
                            dict(value=i, label=np.format_float_positional(i, precision=1))
                            for i in np.arange(0.0, 0.99, 0.1)
                        ],
                    ),
                ]),
            ],
        ),
        dmc.Space(h="sm"),
        dmc.Group(
            grow=True,
            children=[
                dmc.Stack(
                    id="species-matrix-pagination-controls",
                ),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(
            id="species-community-graph",
            figure=empty_figure("Loading data..."),
            # responsive=True,
        ),
    ),
    dmc.Box(
        id="page-content",
        children=get_content("page/species-community")
    ),
])

def register_callbacks():
    from callbacks.pages.species import detection_matrix_callbacks
    detection_matrix_callbacks.register_callbacks()
