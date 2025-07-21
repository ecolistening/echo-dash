import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash_iconify import DashIconify

from typing import List

def ControlsPanel(
    children: List,
    is_open: bool = False,
) -> dmc.Accordion:
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        value=["controls"] if is_open else [],
        children=[
            dmc.AccordionItem(
                value="controls",
                children=[
                    dmc.AccordionControl(
                        "Controls",
                        icon=DashIconify(
                            icon="lsicon:control-outline",
                            color="blue",
                        ),
                    ),
                    dmc.AccordionPanel(
                        pb="1rem",
                        children=children
                    )
                ]
            )
        ],
    )
