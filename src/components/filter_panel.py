import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash_iconify import DashIconify

from typing import List

def FilterPanel(
    children: List,
) -> dmc.Accordion:
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="filters",
                children=[
                    dmc.AccordionControl(
                        "Filters",
                        icon=dmc.ActionIcon(
                            DashIconify(
                                icon="cil:filter",
                                width=24,
                            ),
                            variant="light",
                            color="blue",
                            size="lg",
                        ),
                    ),
                    dmc.AccordionPanel(
                        style={"padding": "0 0 1rem 0"},
                        children=children
                    )
                ]
            )
        ],
    )
