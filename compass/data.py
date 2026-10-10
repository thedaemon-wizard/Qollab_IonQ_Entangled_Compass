"""The two field records (USGS, Boulder observatory, total field F, one value per minute).

The paths are plain string literals on purpose: Qollab ships a data file to the browser only if
its path appears literally in the Python source.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

STORM_PATH = "data/bou_storm_2024-05-10_F.csv"
QUIET_PATH = "data/bou_quiet_2026-10-01_F.csv"

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
    "onset": {
        "path": STORM_PATH,
        "label": "Storm onset, 2024-05-10 16:00 to 19:00 UTC",
        "window": (960, 1141),
    },
}

_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> tuple[list[str], np.ndarray]:
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
    return times, np.array(values)


def load(dataset: str) -> tuple[list[str], np.ndarray]:
    spec = DATASETS[dataset]
    times, f = _read(STORM_PATH if spec["path"] == STORM_PATH else QUIET_PATH)
    if spec["window"]:
        a, b = spec["window"]
        times, f = times[a:b], f[a:b]
    return times, f
