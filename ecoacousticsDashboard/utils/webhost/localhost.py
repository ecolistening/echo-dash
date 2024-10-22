import os

from loguru import logger

class Localhost():
    def __init__(self, sound_file_path):
        self.sound_file_path = sound_file_path
        self.active = os.path.isdir(sound_file_path)

    def is_active(self):
        return self.active

    def get_audio_bytes(self, audio_path):
        print(f"rqst {audio_path}")
        if not self.active:
            logger.warning(f"Accessed host {type(self).__name__} despite being inactive.")

        src_path = os.path.join(self.sound_file_path, audio_path)
        audio_bytes = None
        filetype = None
        
        if os.path.isfile(src_path):
            
            logger.debug(f"Open audio file \'{src_path}\'...")
            with open(src_path, "rb") as file:
                try:
                    audio_bytes = file.read()
                except Exception as e:
                    logger.warning(e)
                    audio_bytes = None
                else:
                    logger.trace(f"Read file {src_path}")
                    filetype = src_path.split('.')[-1]

        return audio_bytes, filetype