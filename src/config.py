import os

from pathlib import Path
from loguru import logger

def is_docker():
    cgroup = Path('/proc/self/cgroup')
    return (
            os.path.exists('/.dockerenv') or
            os.path.isfile(cgroup) and any('docker' in line for line in open(cgroup))
    )

if is_docker():
    root_dir = Path('/data/')
else:
    parent_dir = Path.cwd().parent
    root_dir = parent_dir / "data"

logger.info(f"Data path set to {root_dir}")
