import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import dcc
from dash_iconify import DashIconify

from callbacks.filter import date_filter_callbacks
from callbacks.filter import file_filter_callbacks
from callbacks.filter import site_level_filter_callbacks
from callbacks.filter import acoustic_feature_filter_callbacks
from callbacks.pages import distributions_callbacks

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

PAGE_NAME = 'distributions'
PAGE_TITLE = 'Soundscape Descriptor Distributions'
PLOTHEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Distributions',
)

layout = dmc.Box([
    dcc.Store(id="distributions-graph-data"),
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
                    id="distributions-colour-select",
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="distributions-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="distributions-facet-column-select",
                    label="Facet columns by"
                ),
                dmc.Box([
                    dmc.Chip(
                        'Normalised',
                        id="distributions-normalised-tickbox",
                        value='normalised',
                        checked=False,
                        persistence=True,
                    )
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
                                    graph_data="distributions-graph-data",
                                ),
                                FigureDownloadWidget(
                                    plot_name="distributions-graph",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(
            id="distributions-graph"
        ),
    ),
    dbc.Offcanvas(
        id="distributions-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("distributions"),
    ),
])
