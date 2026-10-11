"""Turn README.md into the Qollab project write-up (dist/writeup.md).

Usage: python scripts/make_writeup.py [git-ref] [--interim] [--check]   (default ref: v1.0-submission)

Relative links point at the public repository at the given ref, and relative images at its raw
files (Qollab shows images from raw.githubusercontent.com). The README's video line
("Demo video (m:ss): <YouTube URL>", optionally in bold) becomes image syntax, which Qollab's
write-up renders as an embedded player; GitHub keeps the plain link. With --interim, a note says
that the repository goes public with the final version, and each image line becomes its alt text
in italics, because the raw files do not open while the repository is private. --check converts
and reports the length without writing dist/writeup.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "thedaemon-wizard/Qollab_IonQ_Entangled_Compass"
LIMIT = 65_000
LOCAL_IMAGE = r"!\[([^\]]*)\]\((?![a-z][a-z0-9+.-]*:|//)([^)]+)\)"
LOCAL_LINK = r"(?<!!)\[([^\]]+)\]\((?![a-z][a-z0-9+.-]*:|//|#)([^)]+)\)"
VIDEO_LINE = (
    r"^(?:\*\*)?Demo video \((\d+:\d{2})\):(?:\*\*)? "
    r"(https://(?:youtu\.be/|(?:www\.)?youtube\.com/watch\?v=)[\w-]+)[ \t]*$"
)


def embed_video(text: str) -> str:
    """Turn the README's video line into image syntax, which Qollab renders as a YouTube player."""
    return re.sub(VIDEO_LINE, lambda m: f"![Demo video ({m.group(1)})]({m.group(2)})", text, flags=re.M)


def _qollab_math(text: str) -> str:
    """GitHub reads ```math fences and $`...`$ (both keep backslashes and * intact); Qollab's
    KaTeX reads $$...$$ and $...$. An inline formula never spans a line."""
    text = re.sub(r"```math\n(.*?)\n```", lambda m: "$$" + m.group(1) + "$$", text, flags=re.S)
    text = re.sub(r"\$`([^`\n]+?)`\$", lambda m: "$" + m.group(1) + "$", text)
    bad = [i for i, ln in enumerate(text.split("\n"), 1) if "$`" in ln or "`$" in ln or ln.count("$") % 2]
    if bad:
        raise ValueError(f"math left unconverted or unpaired on lines {bad}")
    return text


def convert(text: str, ref: str, interim: bool) -> str:
    blob = f"https://github.com/{REPO}/blob/{ref}/"
    raw = f"https://raw.githubusercontent.com/{REPO}/{ref}/"
    text = _qollab_math(text.replace("\r\n", "\n"))
    if interim:
        text = re.sub(LOCAL_IMAGE, lambda m: f"*Figure (shown in the app): {m.group(1)}*", text)
    else:
        text = re.sub(LOCAL_IMAGE, lambda m: f"![{m.group(1)}]({raw}{m.group(2)})", text)
        text = embed_video(text)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert README.md into the Qollab write-up.")
    parser.add_argument("ref", nargs="?", default="v1.0-submission", help="git ref the links point at")
    parser.add_argument("--interim", action="store_true", help="private-repository version, no images")
    parser.add_argument("--check", action="store_true", help="convert and report only; write nothing")
    args = parser.parse_args(argv)
    out = convert((ROOT / "README.md").read_text(encoding="utf-8"), args.ref, args.interim)
    if len(out) > LIMIT:
        print(f"{len(out)} characters, over the {LIMIT} limit", file=sys.stderr)
        return 1
    if args.check:
        print(f"{len(out)} characters; nothing written")
        return 0
    dest = ROOT / "dist" / "writeup.md"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"{len(out)} characters -> dist/writeup.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
