import base64
import os

import dash_bootstrap_components as dbc
from dash import callback, dcc, Input, Output, State, html, no_update, ctx
from loguru import logger

from utils.webhost import AudioAPI
from utils.data import get_path_from_config

def audio_bytes_to_enc(audio_bytes, filetype):
    if audio_bytes is None:
        return ""
    try:
        enc = base64.b64encode(audio_bytes).decode('ascii')
    except Exception as e:
        enc = None
        logger.warning(e)
    else:
        enc = f"data:audio/{filetype};base64," + enc
    return enc

def SoundSampleModal(
    pagename: str
) -> html.Div:
    @callback(
        Output(f'modal_sound_sample_{pagename}', 'is_open'),
        Output(f'modal_sound_header_{pagename}', 'children'),
        Output(f'modal_sound_details_{pagename}', 'children'),
        Output(f'modal_store_filepath_{pagename}', component_property='data'),
        Output(f'modal_sound_file_{pagename}', 'children', allow_duplicate=True),
        Output(f'modal_sound_audio_{pagename}', 'src', allow_duplicate=True),
        Output(f'modal_sound_audio_{pagename}', 'controls', allow_duplicate=True),
        Input(f'{pagename}-graph', component_property='selectedData'),
        State('dataset-select', component_property='value'),
        suppress_callback_exceptions=True,
        prevent_initial_call=True,
    )
    def display_sound_modal(selectedData, dataset):
        logger.debug(f"Trigger ID={ctx.triggered_id}: {selectedData=} {dataset=}")

        if selectedData is None or len(selectedData['points']) == 0:
            logger.debug(f"No point selected.")
            return False, (no_update, no_update, no_update, no_update, no_update, no_update)

        points = selectedData['points']
        if len(points) > 1:
            logger.warning(f'{len(points)} points selected! Only one point will be displayed.')

        pt = points[0]
        logger.debug(f'Selected: {pt}')

        filepath = pt['customdata'][-1]
        filename = filepath.split('/')[-1]

        # [f'Sample #{pt['pointIndex']}']
        return True, pt['hovertext'], [' | '.join(pt['customdata'][:-1])], filepath, f"Looking for \'{filename}\'...", "", False

    @callback(
        Output(f'modal_sound_file_{pagename}', 'children', allow_duplicate=True),
        Output(f'modal_sound_audio_{pagename}', 'src', allow_duplicate=True),
        Output(f'modal_sound_audio_{pagename}', 'controls', allow_duplicate=True),
        Input(f'modal_store_filepath_{pagename}', component_property='data'),
        State('dataset-select', component_property='value'),
        suppress_callback_exceptions=True,
        prevent_initial_call=True,
    )
    def find_sound_file(filepath, dataset):
        filename = filepath.split('/')[-1]
        logger.debug(f"Looking for \'{filename}\'...")
        audio_bytes, filetype, audiopath = AudioAPI.get_audio_bytes(filepath,dataset)
        audiofile = audio_bytes_to_enc(audio_bytes, filetype)

        if audiofile!="":
            output = audiopath.split('/')[-1]
        else:
            output = f"Could not find \'{filename}\'"

        return output, audiofile, audiofile!="", 


    return html.Div([
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Header',id=f'modal_sound_header_{pagename}')),
                dbc.ModalBody([
                    html.H5('Details'),
                    html.Div('',id=f'modal_sound_details_{pagename}'),
                    html.Br(),
                    html.H5('Soundfile'),
                    html.Div('',id=f'modal_sound_file_{pagename}'),
                    html.Audio(id=f'modal_sound_audio_{pagename}', controls=True),
                ]),
                dcc.Store(id=f'modal_store_filepath_{pagename}', data=''),
            ],
            id=f'modal_sound_sample_{pagename}',
            is_open=False,
        ),
    ])
