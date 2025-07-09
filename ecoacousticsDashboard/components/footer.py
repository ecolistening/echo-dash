import dash_mantine_components as dmc

from dash import dcc, html, callback, Input, Output

from utils.content import get_content
from utils.save_plot_fig import get_save_plot

def Tabs(
    PAGE_NAME: str,
    about: bool = True,
    feature: bool = True,
    dataset: bool = True,
) -> html.Div:
    tabs = []
    if about:
        tabs.append(dcc.Tab(label='About', value='about'))
    # if feature:
    #     tabs.append(dcc.Tab(label='Descriptor', value='feature'))
    if dataset:
        tabs.append(dcc.Tab(label='Dataset', value='dataset'))

    tabs_div = html.Div([
        dcc.Tabs(
            id=f'{PAGE_NAME}-tabs',
            value='about',
            children=tabs
        ),
        html.Div(
            id=f'{PAGE_NAME}-tabs-content'
        )
    ])

    @callback(
        Output(f'{PAGE_NAME}-tabs-content', 'children'),
        Input(f'{PAGE_NAME}-tabs', 'value'),
        Input('dataset-select', component_property='value'),
        # FIXME: find a better place to put feature descriptions in the UI
        # Input('feature-dropdown', component_property='value')
    )
    def render_content(
        tab,
        dataset,
        # feature
    ):
        if tab == 'about':
            return get_content(f"page/{PAGE_NAME}")
        # elif tab == 'feature':
        #     return get_content(f"feature/{feature}")
        elif tab == 'dataset':
            return get_content(f"dataset/{dataset}")

    return tabs_div

def Footer(
    PAGE_NAME: str,
    **kwargs,
) -> dmc.Grid:
    return dmc.Grid(
        children=[
            dmc.GridCol([
                Tabs(PAGE_NAME, **kwargs),
            ], span=8),
        ],
    )
