from loguru import logger

# Relative imports from parent directory
import os, sys
from inspect import getsourcefile
current_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))
sys.path.insert(0, current_dir[:current_dir.rfind(os.path.sep)])
from utils.data import get_dataset_names, load_and_filter_dataset
sys.path.pop(0)

def inspect_dataset(dataset):
    data = load_and_filter_dataset(dataset)
    logger.info(f"Dataset {dataset}: {data.shape}")
    logger.info(f"Columns: {list(data.columns)}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    datasets = get_dataset_names()
    parser.add_argument('--dataset', default=datasets[0], choices=datasets)
    args = parser.parse_args()
    inspect_dataset(args.dataset)