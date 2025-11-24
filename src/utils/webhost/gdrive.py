import os
from loguru import logger

from pydrive2.auth import GoogleAuth, AuthenticationError, RefreshError
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFileList

from config import root_dir

def parse_gdrive_path(gd_path):
    if ':' in gd_path:
        gd_path = gd_path.split(':')[1]
    gd_path = gd_path.replace('\\', '/').replace('//', '/')
    if gd_path.startswith('/'):
        gd_path = gd_path[1:]
    if gd_path.endswith('/'):
        gd_path = gd_path[:-1]
    return gd_path.split('/')


class Google_Drive():
    def __init__(self, dataset, sound_file_path):
        self.dataset = dataset
        self.sound_file_path = sound_file_path
        self.key_file = os.path.join(root_dir,dataset,'gdrive-key.json')
        self.active = False
        self.gdrive = None

        if os.path.isfile(self.key_file):
            self.settings = {
                "client_config_backend": "service",
                "service_config": {
                    "client_json_file_path": self.key_file,
                }
            }

            self.authenticate()
        else:
            logger.debug(f"No gdrive key found under \'{self.key_file}\'")

    def resolve_path_to_id(self,folder_path):
        _id = 'root'
        folder_path = parse_gdrive_path(folder_path)

        for idx, folder in enumerate(folder_path):
            folder_list = self.gdrive.ListFile({'q': f"'{_id}' in parents and title='{folder}' and trashed=false", 'fields': 'items(id, title, mimeType)'}).GetList()

            if len(folder_list) < 1:
                logger.debug(f"Empty query for \'{folder}\'")
                return None
            elif len(folder_list) > 1:
                logger.warning(f"More than 1 result for \'{folder}\': {str(folder_list)}")

            _id = folder_list[0]['id']
            title = folder_list[0]['title']
            if idx == (len(folder_path) - 1) and folder == title:
                break
        return _id
            

    def authenticate(self):
        # Create instance of GoogleAuth
        gauth = GoogleAuth(settings=self.settings)

        # Authenticate
        gauth.ServiceAuth()

        try:
            self.gdrive = GoogleDrive(gauth)
        except (AuthenticationError, RefreshError) as e:
            logger.error(e)
            self.active = False
        else:
            logger.debug(f"Authentificated GoogleDrive")
            self.active = True

    def is_active(self):
        return self.active

    def get_audio_bytes(self, audio_path):
        if not self.active:
            logger.warning(f"Accessed host {type(self).__name__} despite being inactive.")

        audio_bytes = None
        filetype = None

        file_path = os.path.join(self.sound_file_path,audio_path)
        logger.trace(f"Resolve gdrive path {file_path}")
        file_id = self.resolve_path_to_id(file_path)
        
        if file_id is not None:
            gfile = self.gdrive.CreateFile({'id': file_id})
            gcontent = gfile.GetContentIOBuffer()
            try:
                audio_bytes = gcontent.read()
            except Exception as e:
                logger.warning(e)
                audio_bytes = None
            else:
                logger.trace(f"Read file {audio_path}")
                filetype = audio_path.split('.')[-1]            
            return audio_bytes, filetype

        return audio_bytes, filetype