from .dataset import stores as dataset_stores
from .filters import stores as filter_stores

stores = [
    *dataset_stores,
    *filter_stores,
]
