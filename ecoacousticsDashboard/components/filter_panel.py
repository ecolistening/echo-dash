import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash_iconify import DashIconify

from typing import List

def FilterPanel(
    children: List,
) -> dmc.Accordion:
    from callbacks import filter_panel_callbacks
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
                        icon=DashIconify(
                            icon="cil:filter",
                            width=24,
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
