#from base64 import b64encode
from dash import dcc
from loguru import logger
from typing import Any, List

def dedup(l: List[Any]) -> List[Any]:
    return list(dict.fromkeys(l))

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
