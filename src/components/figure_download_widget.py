import dash_mantine_components as dmc
import plotly.graph_objects as go

from dash import html, dcc, clientside_callback, callback
from dash import Output, Input, State, ALL, ctx
from dash_iconify import DashIconify
from loguru import logger

from utils import render_fig_as_image_file

def FigureDownloadWidget(
    plot_name: str,
) -> html.Div:

    #############################################################################
    #   Clientside callback to get the current height and width of the chart.   #
    #############################################################################
    clientside_callback(
        """
            function showDetails(n1,n2,n3,n4,plot_name) {
                const triggered = dash_clientside.callback_context.triggered.map(t => t.prop_id)[0];
                var plotDiv = document.getElementById(plot_name);

                var dict = {
                    "trigger": triggered,
                    "height": plotDiv.getBoundingClientRect().height,
                    "width": plotDiv.getBoundingClientRect().width
                }

                return dict;
            } 
        """,
        Output(f"rqst-plot-{plot_name}", "data"),
        Input("dl_jpg", "n_clicks"),
        Input("dl_png", "n_clicks"),
        Input("dl_pdf", "n_clicks"),
        Input("dl_svg", "n_clicks"),
        State(plot_name, "id"),
        prevent_initial_call=True
    )

    @callback(
        Output(f'download-plot-{plot_name}', component_property='data'),
        State('dataset-select', component_property='value'),
        State(plot_name, component_property='figure'),
        Input(f"rqst-plot-{plot_name}", "data"),
        prevent_initial_call=True,
    )
    def download_fig(dataset, fig_dict, rqst):
        logger.debug(f"Trigger Callback: {dataset=} {rqst=}")
        fig = go.Figure(fig_dict)
        fig.update_layout(width=rqst['width'], height=rqst['height'])
        return render_fig_as_image_file(fig,rqst['trigger'],f"{plot_name.strip('-graph')}_{dataset}_plot")

    return dmc.HoverCard(
        children=[
            dmc.HoverCardTarget(
                children=dmc.ActionIcon(
                    DashIconify(
                        icon="uil:image-download",
                        width=24,
                    ),
                    id="image-download-icon",
                    variant="light",
                    color="blue",
                    size="lg",
                    n_clicks=0,
                ),
            ),
            dmc.HoverCardDropdown(
                children=[
                    dmc.Text("Download plot image..."),
                    html.Div([
                        dcc.Store(id=f'rqst-plot-{plot_name}'),
                        dcc.Download(id=f'download-plot-{plot_name}'),
                        dmc.Group(
                            grow=True,
                            children=[
                                dmc.Button("JPG", variant="filled", id='dl_jpg'),
                                dmc.Button("PNG", variant="filled", id='dl_png'),
                                dmc.Button("SVG", variant="filled", id='dl_svg'),
                                dmc.Button("PDF", variant="filled", id='dl_pdf'),
                            ]
                        ),
                    ])
                ]
            )
        ],
    )
