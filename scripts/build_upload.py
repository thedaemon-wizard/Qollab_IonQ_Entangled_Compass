"""Bundle the files Qollab needs into dist/qollab_upload.zip (tests, scripts and docs stay in
the repository only).

Usage: python scripts/build_upload.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ["index.html", "main.js", "main.css", "README.md", "LICENSE", "requirements.txt"]
GLOBS = ["compass/*.py", "ui/*.js", "data/*.csv"]
MAX_FILES, MAX_BYTES, MAX_README = 100, 2_000_000, 65_000


def files() -> list[Path]:
    out = [ROOT / f for f in INCLUDE]
    for g in GLOBS:
        out += sorted(ROOT.glob(g))
    return out


def main() -> int:
    paths = files()
    if len(paths) > MAX_FILES:
        print(f"{len(paths)} files, over the limit of {MAX_FILES}", file=sys.stderr)
        return 1
    for p in paths:
        if p.stat().st_size > MAX_BYTES:
            print(f"{p.name} is over {MAX_BYTES} bytes", file=sys.stderr)
            return 1
    if len((ROOT / "README.md").read_text(encoding="utf-8")) > MAX_README:
        print("README.md is over the 65,000 character limit", file=sys.stderr)
        return 1
    dest = ROOT / "dist" / "qollab_upload.zip"
    dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, p.relative_to(ROOT).as_posix())
    print(f"{len(paths)} files, {sum(p.stat().st_size for p in paths)} bytes -> dist/qollab_upload.zip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
