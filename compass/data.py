"""The two field records (USGS, Boulder observatory, total field F, one value per minute).

The paths are plain string literals on purpose: Qollab ships a data file to the browser only if
its path appears literally in the Python source.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import numpy as np

STORM_PATH = "data/bou_storm_2024-05-10_F.csv"
QUIET_PATH = "data/bou_quiet_2026-10-01_F.csv"
TUCSON_STORM_PATH = "data/tuc_storm_2024-05-10_F.csv"

DATASETS = {
    "quiet": {
        "path": QUIET_PATH,
        "label": "Quiet day, 2026-10-01 (adjusted data)",
        "window": None,
    },
    "storm": {
        "path": STORM_PATH,
        "label": "G5 storm, 2024-05-10 to 05-11 (quasi-definitive data)",
        "window": None,
    },
}

_ROOT = Path(__file__).resolve().parent.parent


@cache
def _read_cached(path: str) -> tuple[tuple[str, ...], np.ndarray]:
    times, values = _parse(path)
    arr = np.array(values)
    arr.setflags(write=False)
    return tuple(times), arr


def _read(path: str) -> tuple[list[str], np.ndarray]:
    """Parsed once per path (the literal path strings above stay in the source)."""
    times, arr = _read_cached(path)
    return list(times), arr.copy()


def _parse(path: str) -> tuple[list[str], list[float]]:
    p = Path(path)
    if not p.exists():  # running from elsewhere (tests): resolve against the project root
        p = _ROOT / path
    times, values = [], []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("time"):
            continue
        t, v = line.split(",")
        if v == "":
            raise ValueError(f"{path}: missing value at {t}")
        times.append(t)
        values.append(float(v))
    return times, values


def load(dataset: str) -> tuple[list[str], np.ndarray]:
    spec = DATASETS[dataset]
    times, f = _read(STORM_PATH if spec["path"] == STORM_PATH else QUIET_PATH)
    if spec["window"]:
        a, b = spec["window"]
        times, f = times[a:b], f[a:b]
    return times, f


def load_pair() -> tuple[list[str], np.ndarray, np.ndarray]:
    """The storm at Boulder and at Tucson (about 1,000 km apart), minute by minute."""
    t_a, f_a = _read(STORM_PATH)
    t_b, f_b = _read(TUCSON_STORM_PATH)
    if t_a != t_b:
        raise ValueError("the two storm records do not share the same minutes")
    return t_a, f_a, f_b
