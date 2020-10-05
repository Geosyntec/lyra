from pathlib import Path
from typing import Any, Dict, Union

import yaml

from lyra.core.cache import cache_decorator

PathType = Union[Path, str]


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _load_file(filepath: PathType) -> str:
    fp = Path(filepath)
    return fp.read_text(encoding="utf-8")


def load_file(filepath: PathType) -> str:
    """wrapper to ensure the cache is called with an absolute path"""
    contents: str = _load_file(Path(filepath).resolve())
    return contents


def load_cfg(filepath: PathType) -> Dict[str, Any]:
    """load cached yaml file"""
    f = load_file(filepath)
    contents: Dict[str, Any] = yaml.safe_load(f)
    return contents
