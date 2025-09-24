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
from components.acoustic_feature_filter import AcousticFeatureFilter
from components.figure_download_widget import FigureDownloadWidget
from components.footer import Footer

PAGE_NAME = "species-by-site"
PAGE_TITLE = "Species by Site"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Species Community',
)

layout = dmc.Box([
    dcc.Store(id="species-community-graph-data"),
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
                    id="species-community-axis-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Site Level", "Spatial"),
                    label="Column facet 1 by...",
                    value="location",
                ),
                DatasetOptionsSelect(
                    id="species-community-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Time of Day", "Temporal"),
                    label="Column facet 2 by...",
                    value="dddn",
                ),
                DatasetOptionsSelect(
                    id="species-community-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    options=("Species Habitat", "Functional Groups"),
                    label="Row facet by...",
                ),
                dmc.Stack([
                    dmc.Text(
                        children="Detection Threshold",
                        size="sm",
                        ta="right",
                    ),
                ]),
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
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(
            id="species-community-graph",
        ),
    ),
    dbc.Offcanvas(
        id="species-community-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("species-community"),
    ),
])

def register_callbacks():
    from callbacks.pages import species_community_callbacks
    species_community_callbacks.register_callbacks()
