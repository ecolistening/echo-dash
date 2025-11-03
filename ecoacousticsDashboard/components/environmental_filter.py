import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import numpy as np

from dash import dcc, callback, no_update
from dash import Input, Output, State
from loguru import logger
from typing import Any, Dict, List, Tuple
from utils import floor, ceil

def EnvironmentalFilterSliderAccordion(
    group: str,
    items: List[Dict[str, str]],
) -> dmc.Accordion:
    return dmc.Stack(
        children=[
            dmc.Stack([
                dmc.Text(
                    option["label"],
                    size="sm",
                    fw=500,
                    ta="left",
                ),
                dmc.Text(
                    f"Current Range: {option['min']} - {option['max']}",
                    id={"type": "weather-variable-range-text", "index": option["value"]},
                    size="sm",
                    ta="left",
                ),
                dmc.Group(
                    justify="space-between",
                    children=[
                        dmc.RangeSlider(
                            id={"type": "weather-variable-range-slider", "index": option["value"]},
                            min=0,
                            max=999,
                            value=[0, 999],
                            marks=[
                                dict(
                                    value=i - 1,
                                    label=str(option["min"] + i/1000 * (option["max"] - option["min"]))
                                )
                                for i in np.linspace(1, 1000, 5, dtype=int)
                            ],
                            persistence=True,
                            style={"flexGrow": 1},
                        ),
                        dmc.Button(
                            id={"type": "weather-variable-reset", "index": option["value"]},
                            children="Reset",
                            color="blue",
                            w=100,
                        ),
                    ]
                )
            ])
            for option in items
        ]
    )

def EnvironmentalFilter() -> dmc.Accordion:
    return dmc.Box(
        children=[
            dmc.Stack(
                id="weather-variable-filter-groups",
                children=[]
            ),
            dmc.Space(h="md"),
            dmc.Group(
                justify="flex-end",
                children=[
                    dmc.Button(
                        id="weather-filter-reset-all",
                        children="Reset Weather",
                        color="blue",
                        w=200
                    )
                ]
            ),
        ],
    )
