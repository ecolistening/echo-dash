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

PAGE_NAME = "species-richness"
PAGE_TITLE = "Species Richness by Time of Day"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Species Richness"
)

PLOT_HEIGHT = 800

plot_types = ["Scatter", "Scatter Polar"]

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
        # TODO:
        # dmc.Space(h=10),
        # dmc.Group(
        #     align="start",
        #     grow=True,
        #     children=[
        #         SpeciesFilter(),
        #     ]
        # ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                dmc.Select(
                    id="species-richness-plot-type-select",
                    label="Select plot type",
                    value="Scatter Polar",
                    data=[
                        dict(value=plot_type, label=plot_type)
                        for plot_type in plot_types
                    ],
                    searchable=True,
                    clearable=False,
                    style=dict(width=200),
                    persistence=True,
                ),
                DatasetOptionsSelect(
                    id="species-richness-color-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="species-richness-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by",
                ),
                DatasetOptionsSelect(
                    id="species-richness-facet-column-select",
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
                                DataDownloadWidget(
                                    context="species-richness",
                                ),
                                FigureDownloadWidget(
                                    plot_name="species-richness-graph",
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
                        min=0.0, max=1.0,
                        step=0.1,
                        value=0.5,
                        persistence=True,
                        marks=[
                            dict(value=i, label=np.format_float_positional(i, precision=1))
                            for i in np.arange(0.0, 1.0, 0.1)
                        ],
                    ),
                ]),
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(id="species-richness-graph"),
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/species-richness")
    ),
])

def register_callbacks():
    from callbacks.pages import species_richness_callbacks
    species_richness_callbacks.register_callbacks()
