import base64
import os

import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State, html, no_update
from loguru import logger

from utils.data import get_path_from_config

def get_modal_sound_sample(pagename):
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

def get_audio_file(name,dataset):

    # temporary add sample file before config is adjusted
    #name = 'sample.wav'

    sound_file_path = get_path_from_config(dataset,'Sound Files','sound_file_path')
    if sound_file_path is None:
        logger.debug("No sound file path found.")
        return ""

    audio_path = os.path.join(sound_file_path,name)
    if not os.path.isfile(audio_path):
        logger.warning(f"No audio file found at \'{audio_path}\'")
        return ""

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

    return enc 

def get_modal_state(selectedData,dataset):
    '''
    Gets most of the output values for the sound file modal, sound details have to be extracted seperately from the data.
    
    returns isSelected, (is_open, sample_no, sound_file_name, sound_file_src, sound_file_ctrl, [modal_sound_details (only if selected data is empty)])

    Callback structure should be as follows:

    @callback(
        Output(f'modal_sound_sample_{PAGENAME}', 'is_open'),
        Output(f'modal_sound_header_{PAGENAME}', 'children'),
        Output(f'modal_sound_file_{PAGENAME}', 'children'),
        Output(f'modal_sound_audio_{PAGENAME}', 'src'),
        Output(f'modal_sound_audio_{PAGENAME}', 'controls'),
        Output(f'modal_sound_details_{PAGENAME}', 'children'),
        
        Input(f'{PAGENAME}-graph', component_property='selectedData'),

        State('dataset-select', component_property='value'),

        suppress_callback_exceptions=True,
        prevent_initial_call=True,
    )
    '''

    if selectedData is None or len(selectedData['points']) == 0:
        return False, (no_update, no_update, no_update, no_update, no_update, no_update)
    
    points = selectedData['points']
    if len(points) > 1:
        logger.warning(f'{len(points)} points selected! Only one point will be displayed.')

    pt = points[0]
    logger.debug(f'Selected: {pt}')

    idx = pt['pointIndex']
    filename = pt['hovertext']
    audiopath = get_audio_file(filename,dataset)

    return True, (True, [f'Sample #{idx}'], [filename], audiopath, audiopath!="")