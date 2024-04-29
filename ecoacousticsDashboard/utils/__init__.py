from loguru import logger

def list2tuple(arr):
    if isinstance(arr,tuple):
        return arr
    
    if not isinstance(arr,list):
        logger.error(f"Unknown type {type(arr)}")
        return arr
    
    # Iterate through nested lists to get all elements
    val = []
    rem = [arr]
    while len(rem)>0:
        obj = rem.pop(0)
        if isinstance(obj,list):
            for el in obj:
                rem.append(el)
        else:
            val.append(obj)
    return tuple(val)

import inspect
from utils.data import load_and_filter_dataset as load_and_filter_dataset_new
from utils.data import load_and_filter_sites as load_and_filter_sites_new
from utils.data import load_config as load_config_new
from utils.data import get_path_from_config as get_path_from_config_new

def load_and_filter_dataset(*args, **kwargs):
    logger.warning(f"Using utils.{inspect.currentframe().f_code.co_name} is deprecated, use utils.data.{inspect.currentframe().f_code.co_name} instead.")
    return load_and_filter_dataset_new(*args, **kwargs)

def load_and_filter_sites(*args, **kwargs):
    logger.warning(f"Using utils.{inspect.currentframe().f_code.co_name} is deprecated, use utils.data.{inspect.currentframe().f_code.co_name} instead.")
    return load_and_filter_sites_new(*args, **kwargs)

def load_config(*args, **kwargs):
    logger.warning(f"Using utils.{inspect.currentframe().f_code.co_name} is deprecated, use utils.data.{inspect.currentframe().f_code.co_name} instead.")
    return load_config_new(*args, **kwargs)

def get_path_from_config(*args, **kwargs):
    logger.warning(f"Using utils.{inspect.currentframe().f_code.co_name} is deprecated, use utils.data.{inspect.currentframe().f_code.co_name} instead.")
    return get_path_from_config_new(*args, **kwargs)