import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import numpy as np

from dash import dcc, callback, no_update
from dash import Input, Output, State
from typing import Any, Dict, List, Tuple
from utils import floor, ceil

def EnvironmentalFilterSliderAccordion(
    group: str,
    items: List[Dict[str, str]],
) -> dmc.Accordion:
    return dmc.Stack(
        children=[
            dmc.Box([
                dmc.Text(
                    option["label"],
                    size="sm",
                    ta="left"
                ),
                dmc.Group(
                    justify="space-between",
                    children=[
                        dmc.RangeSlider(
                            id={"type": "weather-variable-range-slider", "index": option["value"]},
                            min=floor(option["min"]),
                            max=ceil(option["max"]),
                            marks=[
                                dict(value=val, label=str(val))
                                for val in np.linspace(floor(option["min"]), ceil(option["max"]), 10, dtype=int)
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
            if option["min"] != option["max"]
        ]
    )

def EnvironmentalFilter() -> dmc.Accordion:
    return dmc.Box(
        children=[
            dmc.Text("By Weather", size="md", ta="left"),
            dmc.Space(h="sm"),
            dmc.Stack(
                id="weather-variable-filter-groups",
                children=[]
            )
        ],
    )
