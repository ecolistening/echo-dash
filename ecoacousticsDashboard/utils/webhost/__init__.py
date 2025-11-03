import base64
import os

from loguru import logger

from utils.webhost.localhost import Localhost
from utils.webhost.gdrive import Google_Drive

class AudioAPI:
    API = {}

    @classmethod
    def get_hosts(cls, dataset, config):
        if not dataset in cls.API:
            hosts = {}

            audio_path = config.get("Dataset", {}).get("audio_path", None)
            if audio_path is not None:
                host = Localhost(audio_path)
                if host.is_active():
                    hosts['local'] = host

            google_audio_path = config.get("Dataset", {}).get("audio_path", None)
            if google_audio_path is not None:
                host = Google_Drive(dataset, google_audio_path)
                if host.is_active():
                    hosts['gdrive'] = host

            cls.API[dataset] = hosts

        return cls.API[dataset]

    @classmethod
    def get_audio_bytes(cls, name, dataset, config):
        audio_path = name
        hosts = cls.get_hosts(dataset, config)

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
