import argparse
import datetime as dt
import pandas as pd
import time
import shutil
import tempfile

from pathlib import Path
from loguru import logger
from typing import Any, Dict, Tuple, List

def pivot_features(
    data_path: Path,
    save_dir: str | Path | None = None,
    **kwargs: Any,
) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        logger.info(f"Created directory {tmp_dir} as temporary target")
        if data_path.is_file():
            data = pd.read_parquet(data_path)
            logger.info(f"Pivoting {data_path}")
            data = data.pivot(
                index=data.columns[~data.columns.isin(["feature", "value"])],
                columns='feature',
                values='value',
            ).reset_index()
            data.to_parquet(tmp_dir / data_path.name)
            data.to_parquet(acoustic_features_path)
        elif data_path.is_dir():
            for data_file_path in data_path.glob("*.parquet"):
                logger.info(f"Pivoting {data_file_path} and saving to {tmp_dir / data_file_path.name}")
                data = pd.read_parquet(data_file_path)
                data = data.pivot(
                    index=data.columns[~data.columns.isin(["feature", "value"])],
                    columns='feature',
                    values='value',
                ).reset_index()
                data.to_parquet(tmp_dir / data_file_path.name)
        logger.info(f"Moving files from {tmp_dir} to {data_path}")
        for data_file_path in tmp_dir.glob("*.parquet"):
            shutil.copy(tmp_dir / data_file_path.name, data_path / data_file_path.name)

def main(
    data_path: Path,
) -> None:
    start_time = time.time()

    pivot_features(data_path=data_path)

    logger.info(f"Pivot complete")
    logger.info(f"Time taken: {str(dt.timedelta(seconds=time.time() - start_time))}")

def get_base_parser():
    parser = argparse.ArgumentParser(
        description="Pivot acoustic features table(s)",
        add_help=False,
    )
    parser.add_argument(
        "--data-path",
        type=lambda p: Path(p),
        help="Parquet file or directory of acoustic feature parquet files to pivot."
    )
    return parser

if __name__ == '__main__':
    parser = get_base_parser()
    args = parser.parse_args()
    main(**vars(args))

