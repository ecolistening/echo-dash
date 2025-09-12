import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

def DateRangeFilter():
    return dmc.Accordion(
        id="date-filter-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="date-range",
                children=[
                    dmc.AccordionControl("Date Range"),
                    dmc.AccordionPanel(
                        children=[
                            dmc.Stack(
                                justify="flex-start",
                                children=[
                                    dmc.Text("Filter by Date"),
                                    dmc.DatePicker(
                                        id="date-picker",
                                        type="range",
                                        persistence=True,
                                        allowDeselect=False,
                                    ),
                                ]
                            ),
                        ]
                    )
                ]
            )
        ],
    )
