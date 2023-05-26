from pathlib import Path

def is_docker():
    cgroup = Path('/proc/self/cgroup')
