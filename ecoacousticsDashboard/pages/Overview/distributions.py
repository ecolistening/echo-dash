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
from components.figure_download_widget import FigureDownloadWidget
from utils.content import get_content

PAGE_NAME = 'distributions'
PAGE_TITLE = 'Soundscape Descriptor Distributions'
PLOTHEIGHT = 800

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Distributions',
)

layout = dmc.Box([
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
                    id="distributions-colour-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Colour by",
                    value="sitelevel_1",
                ),
                DatasetOptionsSelect(
                    id="distributions-facet-row-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet rows by",
                ),
                DatasetOptionsSelect(
                    id="distributions-facet-column-select",
                    action=FETCH_DATASET_DROPDOWN_OPTION_GROUPS,
                    label="Facet columns by",
                    value="dddn",
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
                                    context="distributions",
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
            ],
        ),
    ]),
    dmc.Space(h="sm"),
    dcc.Loading(
        dcc.Graph(
            id="distributions-graph"
        ),
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="page-content",
        children=get_content("page/acoustic-feature-distributions")
    ),
    dmc.Space(h="sm"),
    dmc.Box(
        id="feature-descriptor-content",
        children=[],
    ),
])

def register_callbacks():
    from callbacks.pages import distributions_callbacks
    distributions_callbacks.register_callbacks()
