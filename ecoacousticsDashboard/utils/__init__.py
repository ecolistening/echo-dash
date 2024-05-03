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