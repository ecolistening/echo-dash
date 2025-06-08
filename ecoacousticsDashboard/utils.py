from typing import Any, List

def dedup(l: List[Any]) -> List[Any]:
    return list(dict.fromkeys(l))
