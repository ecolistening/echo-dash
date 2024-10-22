import base64
import os

from loguru import logger

from utils.data import get_path_from_config
from utils.webhost.localhost import Localhost
from utils.webhost.gdrive import Google_Drive

# static class
class AudioAPI(object):
    API = {}

    @staticmethod
    def get_hosts(dataset):
        if not dataset in AudioAPI.API:
            hosts = {}

            sound_file_path = get_path_from_config(dataset,'Sound Files','sound_file_path')
            if sound_file_path is not None:
                host = Localhost(sound_file_path)
                if host.is_active():
                    hosts['local'] = host

            sound_file_path = get_path_from_config(dataset,'Sound Files','gdrive_sound_file_path')
            if sound_file_path is not None:
                host = Google_Drive(dataset, sound_file_path)
                if host.is_active():
                    hosts['gdrive'] = host

            AudioAPI.API[dataset] = hosts

        return AudioAPI.API[dataset]

    @staticmethod
    def get_audio_bytes(name, dataset):
        audio_path = name
        hosts = AudioAPI.get_hosts(dataset)

        split_name = os.path.splitext(name)
        audio_path_base = split_name[0]

        for host_name, host in hosts.items():

            # Move file extension to sub class
            for file_extension in ('mp3','MP3','wav','WAV'):
                audio_path = f"{audio_path_base}.{file_extension}"
                audio_bytes, filetype = host.get_audio_bytes(audio_path)
                if audio_bytes is not None:
                    logger.debug(f"Found file \'{audio_path}\' at host \'{host_name}\'")
                    return audio_bytes, filetype, audio_path
         
        else:
            if len(split_name)>0:
                audio_path = f"{audio_path_base}{split_name[1]}"
            logger.warning(f"No audio file found at \'{audio_path}\'")
            return None, None, audio_path