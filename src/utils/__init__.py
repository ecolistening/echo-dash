import base64
import datetime as dt
import hashlib
import numpy as np
import pandas as pd

from dash import dcc
from loguru import logger
from typing import Any, Dict, List

def ceil(a, precision=0):
    return np.round(a + 0.5 * 10**(-precision), precision)

def floor(a, precision=0):
    return np.round(a - 0.5 * 10**(-precision), precision)

def float_to_index(x: float, min_val: float, max_val: float, n_steps: int = 1000):
    return int(round((x - min_val) / (max_val - min_val) * (n_steps - 1)))

def index_to_float(i: int, min_val: float, max_val: float, n_steps: int = 1000) -> float:
    return min_val + (i / (n_steps - 1)) * (max_val - min_val)

def hashify(s: str):
    h = hashlib.new("sha256")
    h.update(s.encode("utf-8"))
    return h.hexdigest()

def dedup(l: List[Any]) -> List[Any]:
    return list(dict.fromkeys(l))

def str2date(s: str):
    return dt.datetime.strptime(s, "%Y-%m-%d").date()

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

def render_fig_as_image_file(fig,format_str:str,name:str):
    for format in ('jpg','png','pdf','svg'):
        if format in format_str.lower():
            break
    else:
        logger.error(f"Unknown format string \"{format_str}\"")
        return None
    
    img_bytes = fig.to_image(format=format)
    # encoding = b64encode(img_bytes).decode()
    # img_b64 = f"data:image/{format};base64," + encoding

    return dcc.send_bytes(img_bytes, f"{name}.{format}")

def audio_bytes_to_enc(
    audio_bytes,
    filetype
) -> str:
    if audio_bytes is None:
        return ""
    try:
        enc = base64.b64encode(audio_bytes).decode('ascii')
    except Exception as e:
        enc = None
        logger.warning(e)
    else:
        enc = f"data:audio/{filetype};base64," + enc
    return enc

def capitalise_each(string: str) -> str:
    return ' '.join([s.capitalize() for s in string.split(' ')])

DOWNLOAD_PARAMS = {
    "csv": { "render": lambda df: df.to_csv, "extension": "csv", "params": {}},
    "excel": { "render": lambda df: df.to_excel, "extension": "xlsx", "params": {"sheet_name": "Sheet 1"}},
    "json": { "render": lambda df: df.to_json, "extension": "json", "params": {}},
    "parquet": { "render": lambda df: df.to_parquet, "extension": "parquet", "params": {}},
}
def send_download(df: pd.DataFrame, file_name: str, dl_type: str) -> Dict[str, Any]:
    render, extension, params = DOWNLOAD_PARAMS[dl_type].values()
    file_name = f"{file_name}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    return dcc.send_data_frame(render(df), file_name, **params)

def safe_category_orders(df, category_orders):
    safe_orders = {}
    for key, cats in category_orders.items():
        if key in df.columns:
            safe_orders[key] = [c for c in cats if c in df[key].unique()]
    return safe_orders
