import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import dcc

def EnvironmentalFilter():
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="environmental",
                children=[
                    dmc.AccordionControl("Environmental"),
                    dmc.AccordionPanel(
                        children=[
                            dmc.Stack(
                                justify="flex-start",
                                children=[
                                    dmc.Box(
                                        children=[
                                            dmc.Text("Select a temperature range", size="sm"),
                                            dcc.RangeSlider(
                                                id="temperature-range-slider",
                                                min=0,
                                                max=100,
                                                value=[0, 100],
                                                allowCross=False,
                                            ),
                                        ]
                                    ),
                                    dmc.Box(
                                        children=[
                                            dmc.Text("Select a precipitation range", size="sm"),
                                            dcc.RangeSlider(
                                                id="precipitation-range-slider",
                                                min=0,
                                                max=100,
                                                value=[0, 100],
                                                allowCross=False,
                                            ),
                                        ]
                                    ),
                                    dmc.Box(
                                        children=[
                                            dmc.Text("Select a wind speed range", size="sm"),
                                            dcc.RangeSlider(
                                                id="wind-speed-range-slider",
                                                min=0,
                                                max=100,
                                                value=[0, 100],
                                                allowCross=False,
                                            ),
                                        ]
                                    ),
                                    dmc.Box(
                                        children=[
                                            dmc.Text("Select a snowfall range", size="sm"),
                                            dcc.RangeSlider(
                                                id="snowfall-range-slider",
                                                min=0,
                                                max=100,
                                                value=[0, 100],
                                                allowCross=False,
                                            ),
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
