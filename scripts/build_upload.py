"""Bundle the files Qollab needs into dist/qollab_upload.zip, with the saved run results (tests,
scripts and docs stay in the repository only).

Usage: python scripts/build_upload.py [--card dist/writeup.md] [--check]

--card puts the converted write-up into the bundle as README.md (Qollab shows it as the Project
Card). --check only lists the files and checks the limits; it writes nothing.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# README.md is not shipped as it is: Qollab shows it as the Project Card, so --card puts the converted
# write-up there instead (GitHub math and relative links do not render on Qollab).
INCLUDE = ["index.html", "main.js", "main.css", "LICENSE", "requirements.txt"]
# The saved Qollab runs and the headline numbers ship too, so judges can check the recorded results.
GLOBS = ["compass/*.py", "ui/*.js", "data/*.csv", "results/qollab/*.json", "results/headline_numbers.json"]
MAX_FILES, MAX_BYTES, MAX_README = 100, 2_000_000, 65_000


def files() -> list[Path]:
    out = [ROOT / f for f in INCLUDE]
    for g in GLOBS:
        out += sorted(ROOT.glob(g))
    return out


def check_limits(paths: list[Path], card: Path | None) -> list[str]:
    """Problems with the bundle against Qollab's upload limits (empty when it is fine)."""
    problems = []
    if len(paths) > MAX_FILES:
        problems.append(f"{len(paths)} files, over the limit of {MAX_FILES}")
    problems += [f"{p.name} is over {MAX_BYTES} bytes" for p in paths if p.stat().st_size > MAX_BYTES]
    if card and len(card.read_text(encoding="utf-8")) > MAX_README:
        problems.append(f"{card} is over the {MAX_README:,} character limit")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build dist/qollab_upload.zip for Qollab.")
    parser.add_argument("--card", type=Path, help="write-up to ship as README.md (the Project Card)")
    parser.add_argument("--check", action="store_true", help="list the files and check the limits only")
    args = parser.parse_args(argv)
    card = args.card
    if card and not card.is_file():
        parser.error(f"{card} does not exist")
    paths = files()
    problems = check_limits(paths, card)
    for msg in problems:
        print(msg, file=sys.stderr)
    if args.check:
        for p in paths:
            print(f"{p.stat().st_size:>9}  {p.relative_to(ROOT).as_posix()}")
        if card:
            print(f"{card.stat().st_size:>9}  README.md (from {card})")
        print(f"{len(paths)} files, {sum(p.stat().st_size for p in paths)} bytes; nothing written")
        return 1 if problems else 0
    if problems:
        return 1
    dest = ROOT / "dist" / "qollab_upload.zip"
    dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, p.relative_to(ROOT).as_posix())
        if card:
            z.write(card, "README.md")
    note = f", {card} as README.md" if card else ", no README.md"
    print(f"{len(paths)} files, {sum(p.stat().st_size for p in paths)} bytes{note} -> dist/qollab_upload.zip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
