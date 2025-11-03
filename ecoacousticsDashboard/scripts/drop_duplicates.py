import argparse
import datetime as dt
import pandas as pd
import time
import shutil
import tempfile

from pathlib import Path
from loguru import logger
from typing import Any, Dict, Tuple, List

def drop_duplicates(
    data_path: Path,
    save_dir: str | Path | None = None,
    **kwargs: Any,
) -> None:
    to_delete = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        logger.info(f"Created directory {tmp_dir} as temporary target")
        if data_path.is_file():
            data = pd.read_parquet(data_path)
            data = data.drop_duplicates(subset="file_id")
            data.to_parquet(tmp_dir / data_path.name)
            data.to_parquet(acoustic_features_path)
        elif data_path.is_dir():
            for data_file_path in data_path.glob("*.parquet"):
                logger.info(f"Dropping duplicates in {data_file_path} and saving to {tmp_dir / data_file_path.name}")
                data = pd.read_parquet(data_file_path)
                data = data.drop_duplicates(subset="file_id")
                if len(data):
                    data.to_parquet(tmp_dir / data_file_path.name)
                else:
                    to_delete.append(data_file_path)
        logger.info(f"Moving files from {tmp_dir} to {data_path}")
        for data_file_path in tmp_dir.glob("*.parquet"):
            shutil.copy(tmp_dir / data_file_path.name, data_path / data_file_path.name)

def main(
    data_path: Path,
) -> None:
    start_time = time.time()

    drop_duplicates(data_path=data_path)

    logger.info(f"Task complete")
    logger.info(f"Time taken: {str(dt.timedelta(seconds=time.time() - start_time))}")

def get_base_parser():
    parser = argparse.ArgumentParser(
        description="Drop duplicates in files table(s)",
        add_help=False,
    )
    parser.add_argument(
        "--data-path",
        type=lambda p: Path(p),
        help="Parquet file or directory of parquet files."
    )
    return parser

if __name__ == '__main__':
    parser = get_base_parser()
    args = parser.parse_args()
    main(**vars(args))

