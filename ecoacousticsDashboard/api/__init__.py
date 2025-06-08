import os
import functools
import requests

from dotenv import load_dotenv
from loguru import logger
from typing import Any, Dict, List

load_dotenv()

HOST_NAME = os.environ.get("HOST_NAME", "localhost")
PORT = os.environ.get("PORT", 8050)

BASE_URL = f"http://{HOST_NAME}:{PORT}/api/v1"

FETCH_DATASETS = "fetch_datasets"
SET_CURRENT_DATASET = "set_current_dataaset"
FETCH_DATASET_CONFIG = "fetch_dataset_config"
FETCH_DATASET_SITES_TREE = "fetch_dataset_sites_tree"

API = {
    FETCH_DATASETS: functools.partial(requests.get, f"{BASE_URL}/datasets"),
    SET_CURRENT_DATASET: functools.partial(requests.post, f"{BASE_URL}/dataset"),
    FETCH_DATASET_CONFIG: functools.partial(requests.get, f"{BASE_URL}/dataset/config"),
    FETCH_DATASET_SITES_TREE: functools.partial(requests.get, f"{BASE_URL}/dataset/sites-tree"),
}

def dispatch(
    end_point: str,
    payload: Dict[str, Any] = {},
    default: Any | None = None,
) -> List | Dict[str, Any]:
    try:
        request = API[end_point]
        logger.debug(f"Sending request to {end_point}")
        response = request(json=payload)
        return response.json()
    except:
        logger.debug(f"Request to {end_point} failed")
        return default
