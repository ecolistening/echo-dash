from loguru import logger

# Relative imports from parent directory
import os, sys
from inspect import getsourcefile
current_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))
sys.path.insert(0, current_dir[:current_dir.rfind(os.path.sep)])
from utils.data import get_dataset_names, load_and_filter_dataset
sys.path.pop(0)

os.makedirs(os.path.join(current_dir,'log'),exist_ok=True)
logger.add(os.path.join(current_dir,"log/{time}.log"), rotation="00:00", retention="90 days")

def inspect_dataset(dataset,column=None):
    data = load_and_filter_dataset(dataset)
    logger.info(f"Dataset {dataset}: {data.shape}")
    logger.info(f"Columns: {list(data.columns)}")
    logger.info(f"Features: {list(data.feature.unique())}")

    if column is not None:
        if column in data.columns:
            print(data[column].head)
            print(data[column].iloc[0])
        else:
            logger.warning(f"Can't find column {column}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    datasets = get_dataset_names()
    parser.add_argument('--dataset', type=str,default=datasets[0], choices=datasets)
    parser.add_argument('--column', type=str, default=None)
    args = parser.parse_args()
    inspect_dataset(args.dataset,column=args.column)