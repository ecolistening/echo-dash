import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import dcc, callback, no_update
from dash import Input, Output, State
from typing import Any, Dict, List, Tuple

def EnvironmentalFilterSliderAccordion(
    group: str,
    items: List[Dict[str, str]],
) -> dmc.Accordion:
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value=group,
                children=[
                    dmc.AccordionControl(group),
                    dmc.AccordionPanel(
                        children=dmc.Stack(
                            justify="flex-start",
                            children=[
                                dmc.Box(
                                    children=[
                                        dmc.Text(option["label"], size="sm"),
                                        dcc.RangeSlider(
                                            id={"type": "weather-variable-range-slider", "index": option["value"]},
                                            min=option["min"],
                                            max=option["max"],
                                            value=[option["min"], option["max"]],
                                            allowCross=False,
                                            persistence=True,
                                        ),
                                    ]
                                )
                                for option in items
                            ]
                        )
                    )
                ],
            ),
        ]
    )

def EnvironmentalFilter() -> dmc.Accordion:
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
                        children=dmc.Stack(
                            id="weather-variable-filter-groups",
                            justify="flex-start",
                            children=[]
                        ),
                    )
                ]
            )
        ],
    )
