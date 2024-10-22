# Soundfiles

Selecting individual samples allow the playback of a soundfile if provided. Those can be stored locally on the server or remotely on GoogleDrive. Currently sound formats "wav" and "mp3" are supported.

To store the soundfiles locally, add the path to the soundfiles as 'sound_file_path' to the dataset config or place the soundfiles in a folder 'soundfiles' in the dataset folder.

To store the soundfiles remotely on GoogleDrive, add the service account credentials as 'gdrive-key.json' in the dataset folder and add the path structure as 'gdrive_sound_file_path' to the dataset config. The default path is 'DASHBOARD_MP3/[dataset]/soundfiles'

Default paths are set in 

> ecoacousticsDashboard/utils/data.py:get_path_from_config_lru
