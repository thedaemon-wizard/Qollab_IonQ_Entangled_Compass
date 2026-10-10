"""Turn README.md into the Qollab project write-up (dist/writeup.md).

Usage: python scripts/make_writeup.py [git-ref] [--interim]   (default ref: v1.0-submission)

Relative links point at the public repository at the given ref. With --interim, a note says
that the repository goes public with the final version (its links do not open before that).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "thedaemon-wizard/Qollab_IonQ_Entangled_Compass"
LIMIT = 65_000
LOCAL_LINK = r"(?<!!)\[([^\]]+)\]\((?![a-z][a-z0-9+.-]*:|//|#)([^)]+)\)"


def convert(text: str, ref: str, interim: bool) -> str:
    blob = f"https://github.com/{REPO}/blob/{ref}/"
    text = text.replace("\r\n", "\n")
    text = re.sub(LOCAL_LINK, lambda m: f"[{m.group(1)}]({blob}{m.group(2)})", text)
    if interim:
        marker = f"> Repository: https://github.com/{REPO}\n"
        if marker not in text:
            raise ValueError("repository line not found")
        text = text.replace(
            marker,
            marker
            + ">\n> *Interim version: the repository and its links go public with the final submission.*\n",
            1,
        )
    return text


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = convert(
        (ROOT / "README.md").read_text(encoding="utf-8"),
        args[0] if args else "v1.0-submission",
        "--interim" in sys.argv,
    )
    if len(out) > LIMIT:
        print(f"{len(out)} characters, over the {LIMIT} limit", file=sys.stderr)
        return 1
    dest = ROOT / "dist" / "writeup.md"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"{len(out)} characters -> dist/writeup.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
