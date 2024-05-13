import os
from pathlib import Path

def is_docker():
    cgroup = Path('/proc/self/cgroup')
    return (
            os.path.exists('/.dockerenv') or
            os.path.isfile(cgroup) and any('docker' in line for line in open(cgroup))
    )

if is_docker():
    root_dir = Path('/data/')
else:
    cwd = Path.cwd()
    root_dir = Path(cwd.parents[0], 'data')