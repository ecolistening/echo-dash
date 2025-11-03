import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

def DateRangeFilter():
    return dmc.Box([
        dmc.Text(
            id="date-picker-text",
            size="sm",
            ta="left",
        ),
        dmc.Stack(
            justify="flex-start",
            children=[
                dmc.DatePicker(
                    id="date-picker",
                    type="range",
                    persistence=True,
                    allowDeselect=False,
                    numberOfColumns=4,
                ),
            ]
        ),
        dmc.Space(h="sm"),
        dmc.Group(
            justify="flex-end",
            children=[
                dmc.Button(
                    id="date-picker-reset",
                    children="Reset",
                    color="blue",
                    w=100
                ),
            ]
        )
    ])
