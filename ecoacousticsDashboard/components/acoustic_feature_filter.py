import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import dcc, callback
from dash import Input, Output
from typing import List

from api import dispatch, FETCH_ACOUSTIC_FEATURES

def AcousticFeatureFilter():
    return dmc.Accordion(
        id="feature-filter-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="acoustic-features",
                children=[
                    dmc.AccordionControl("Acoustic Feature"),
                    dmc.AccordionPanel(
                        children=[
                            dmc.Stack(
                                justify="flex-start",
                                children=[
                                    dmc.Box([
                                        dmc.Text("Select an acoustic feature", size="sm"),
                                        dmc.Select(
                                            id="feature-select",
                                            searchable=True,
                                            clearable=False,
                                            allowDeselect=False,
                                            persistence=True,
                                            nothingFoundMessage="No options found...",
                                        ),
                                    ]),
                                    dmc.Divider(
                                        variant="solid",
                                        orientation="vertical",
                                    ),
                                    dmc.Box(
                                        # m=10,
                                        children=[
                                            dmc.Text("Select a value range", size="sm"),
                                            dcc.RangeSlider(
                                                id="feature-range-slider",
                                                min=0,
                                                max=100,
                                                persistence=True,
                                                allowCross=False,
                                            ),
                                            dmc.Box(
                                                children=[
                                                    dmc.Text(
                                                        "Current Range: ",
                                                        size="sm",
                                                        span=True
                                                    ),
                                                    dmc.Text(
                                                        id="feature-range-bounds",
                                                        size="sm",
                                                        span=True
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    )
                ]
            )
        ],
    )
