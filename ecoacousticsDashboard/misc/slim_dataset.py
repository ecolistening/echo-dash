import os
import os.path as path
import random
import shutil
import sys

import pyarrow as pa
import pyarrow.parquet as pq

# Relative imports from parent directory
from inspect import getsourcefile
current_dir = path.dirname(path.abspath(getsourcefile(lambda:0)))
sys.path.insert(0, current_dir[:current_dir.rfind(path.sep)])
from config import root_dir
sys.path.pop(0)


def slim_dataset(dataset,datapoints):
    path_src = path.join(root_dir, dataset)
    path_dst = path.join(root_dir, dataset+'_slim')
    os.makedirs(path_dst,exist_ok=True)
    
    print(f"Copying config.ini..")
    shutil.copyfile(path.join(path_src, 'config.ini'), path.join(path_dst, 'config.ini'))

    print(f"Copying locations.parquet..")
    shutil.copyfile(path.join(path_src, 'locations.parquet'), path.join(path_dst, 'locations.parquet'))

    print(f"Loading {dataset}/indices.parquet..")
    tab = pq.read_table(path.join(path_src, 'indices.parquet'))
    num_rows = tab.num_rows

    print(f"Selecting {datapoints}/{num_rows} rows from dataset {dataset}..")
    indeces = pa.array(random.sample(range(num_rows), datapoints))
    tab_filter = tab.take(indeces)

    print(f"Writing {dataset}_slim/indices.parquet..")
    pq.write_table(tab_filter, path.join(path_dst, 'indices.parquet'))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    datasets = [d.name for d in root_dir.glob("*") if d.is_dir()]
    parser.add_argument('--dataset', default='sounding_out', choices=datasets)
    parser.add_argument('--datapoints', default=1234, type=int)
    args = parser.parse_args()
    slim_dataset(args.dataset,args.datapoints)
