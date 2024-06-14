import base64
import os

import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State, html, no_update, ctx
from loguru import logger

from utils.data import get_path_from_config

def get_audio_file(name,dataset):

    sound_file_path = get_path_from_config(dataset,'Sound Files','sound_file_path')
    if sound_file_path is None:
        logger.debug("No sound file path found.")
        return "", name

    split_name = os.path.splitext(name)

    audio_path_base = os.path.join(sound_file_path,split_name[0])

    for file_extension in ('wav','WAV','mp3','MP3'):
        audio_path = f"{audio_path_base}.{file_extension}"
        if os.path.isfile(audio_path):
            break
    else:
        if len(split_name)>0:
            audio_path = f"{audio_path_base}{split_name[1]}"
        logger.warning(f"No audio file found at \'{audio_path}\'")
        return "", audio_path

    logger.debug(f"Open audio file \'{audio_path}\'...")
    try:
        enc = base64.b64encode(open(audio_path, "rb").read()).decode('ascii')
    except Exception as e:
        enc = ""
        logger.warning(f"Can't read file \"{audio_path}\".")
    else:
        filetype = name.split('.')[-1]
        enc = f"data:audio/{filetype};base64," + enc
        logger.info(f"Read audio file {name} from dataset {dataset}.")

    return enc, audio_path

def get_modal_sound_sample(pagename):

    @callback(
        Output(f'modal_sound_sample_{pagename}', 'is_open'),
        Output(f'modal_sound_header_{pagename}', 'children'),
        Output(f'modal_sound_file_{pagename}', 'children'),
        Output(f'modal_sound_audio_{pagename}', 'src'),
        Output(f'modal_sound_audio_{pagename}', 'controls'),
        Output(f'modal_sound_details_{pagename}', 'children'),
        
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

        filename = pt['customdata'][-1]
        audiofile, audiopath = get_audio_file(filename,dataset)

        # [f'Sample #{pt['pointIndex']}']
        return True, pt['hovertext'], audiopath.split('/')[-1], audiofile, audiofile!="", [' | '.join(pt['customdata'][:-1])]

    modal_sound_sample = html.Div(
        [
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
                ],
                id=f'modal_sound_sample_{pagename}',
                is_open=False,
            ),
        ]
    )
    return modal_sound_sample