"""Download the three field records the app replays, from the USGS geomagnetism web service.

Usage: python scripts/fetch_usgs.py

Writes data/bou_storm_2024-05-10_F.csv and data/tuc_storm_2024-05-10_F.csv (quasi-definitive,
2 days) and data/bou_quiet_2026-10-01_F.csv (adjusted, 1 day): Boulder (BOU) and Tucson (TUC)
observatories, total field F in nT, one value per minute, exactly as served (no rounding, no gap
filling; a missing value would be written as an empty field and the app refuses such a file).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://geomag.usgs.gov/ws/data/"
RECORDS = [
    ("BOU", "bou_storm_2024-05-10_F.csv", "2024-05-10T00:00:00Z", "2024-05-11T23:59:00Z", "quasi-definitive"),
    ("BOU", "bou_quiet_2026-10-01_F.csv", "2026-10-01T00:00:00Z", "2026-10-01T23:59:00Z", "adjusted"),
    ("TUC", "tuc_storm_2024-05-10_F.csv", "2024-05-10T00:00:00Z", "2024-05-11T23:59:00Z", "quasi-definitive"),
]
NAMES = {"BOU": "Boulder", "TUC": "Tucson"}
CREDIT = (
    "Geomagnetic data: USGS Geomagnetism Program, {name} ({code}) observatory, courtesy of the "
    "U.S. Geological Survey. Thanks to INTERMAGNET (www.intermagnet.org) for promoting high "
    "standards of magnetic observatory practice."
)
POLICY = "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits"
LICENCE = (
    "USGS-authored or produced data are considered to be in the U.S. Public Domain (USGS policy "
    f'"Copyrights and Credits", {POLICY}, read 2026-10-11); USGS asks for credit (line above). '
    "Not covered by this project's MIT licence."
)


def fetch(station: str, start: str, end: str, data_type: str) -> tuple[str, dict]:
    url = (
        f"{BASE}?id={station}&starttime={start}&endtime={end}&elements=F&sampling_period=60"
        f"&type={data_type}&format=json"
    )
    with urllib.request.urlopen(url, timeout=60) as resp:
        return url, json.load(resp)


def main() -> int:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")
    for station, name, start, end, data_type in RECORDS:
        url, doc = fetch(station, start, end, data_type)
        (series,) = [v for v in doc["values"] if v["id"] == "F"]
        times, values = doc["times"], series["values"]
        if len(times) != len(values):
            raise ValueError(f"{name}: {len(times)} times but {len(values)} values")
        lines = [
            f"# Source: USGS geomagnetism web service, observatory {station} ({NAMES[station]}), element F"
            " (total field, nT), 1-minute",
            f"# URL: {url}",
            f"# Data type: {data_type}; retrieved {now}; values as served",
            f"# Credit: {CREDIT.format(name=NAMES[station], code=station)}",
            f"# Licence: {LICENCE}",
            "time_utc,F_nT",
        ]
        lines += [f"{t[:16]},{'' if v is None else v}" for t, v in zip(times, values, strict=True)]
        (ROOT / "data" / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        missing = sum(v is None for v in values)
        kind = doc["metadata"]["intermagnet"].get("data_type")
        print(f"{name}: {len(values)} rows, {missing} missing, {kind}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
