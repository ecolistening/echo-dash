import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

def DateRangeFilter():
    return dmc.Stack(
        justify="flex-start",
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Text("By Date", size="md", ta="left"),
                    dmc.Button(
                        id="date-picker-reset",
                        children="Reset",
                        color="blue",
                        w=100
                    )
                ]
            ),
            dmc.DatePicker(
                id="date-picker",
                type="range",
                persistence=True,
                allowDeselect=False,
                numberOfColumns=4,
            ),
        ]
    )
