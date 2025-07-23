import attrs
import numpy as np
import hashlib
import cachetools
from dataclasses import dataclass
from datetime import date
import pathlib
import itertools
from functools import lru_cache, cached_property
import os
from typing import List

import bigtree as bt
from loguru import logger
import pandas as pd
from urllib.parse import quote, unquote

from configparser import ConfigParser
from config import root_dir
from utils import list2tuple
from utils import query as Q
from utils.umap import umap_data

from typing import Any, Callable, Dict, List, Tuple, Iterable

def get_path_from_config(dataset: str, config: Dict[str, Any], section: str, option:str):
    '''
        Gets a path stored as 'option' in the 'section' of the config of a given 'dataset'.

        Storing result in cache brings the risk that changes in the config will not be effective until reset or cache is filled.
    '''
    logger.debug(f"Extract path \'{option}\' from config section \'{section}\' for dataset \'{dataset}\'..")

    extract_path = None
    if (section := config.get(section, None)):
        extract_path = section.get(option, None)
        logger.debug(f"Extracted path \'{extract_path}\'")
        if extract_path and not os.path.isabs(extract_path):
            extract_path = os.path.join(root_dir,dataset,extract_path)
            logger.debug(f"Transformed path: \'{extract_path}\'")
    else:
        logger.debug(f"Could not find path in config.")
        if option=='sound_file_path':
            path_ = os.path.join(root_dir,dataset,'soundfiles')
            if os.path.isdir(path_):
                extract_path = path_
                logger.debug(f"Found default path \'{extract_path}\'")
        if option=='gdrive_sound_file_path':
            extract_path = os.path.join("DASHBOARD_MP3",dataset,'soundfiles')

    return extract_path
