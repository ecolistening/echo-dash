import dash_mantine_components as dmc

from dash import html

def SizeSlider(
    id: str,
    default: int = 3,
) -> html.Div:
    return html.Div([
        dmc.Text('Dot Size', size='sm', align='right'),
        dmc.Slider(
            id=id,
            min=1,
            max=20,
            step=1,
            value=default,
            marks=[
                {"value": i, "label": f"{i}"} for i in (1, 10, 20)
            ],
            persistence=True
        )
    ])

