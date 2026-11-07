#!/usr/bin/env python3
"""Screenshot des Sakuna-Fensters -> docs/<name>.png (3840x2160 zugeschnitten).

Aufruf im Terminal neben dem Spiel:
    python3 capture.py dialog          -> docs/dialog.png
    python3 capture.py dialog --look   -> nur ansehen nach /tmp, nichts speichern

Sucht das Sakuna-Fenster automatisch (auch nach einem Neustart).
"""
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
GAME_W, GAME_H = 3840, 2160


def find_window():
    out = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "sakuna" in line.lower():
            return line.split()[0]
    return None


def capture(wid, out_path):
    tmp = "/tmp/_capture_raw.png"
    subprocess.run(["magick", "import", "-window", wid, tmp], check=True)
    im = Image.open(tmp)
    # Spiel rendert 3840x2160 zentriert im Fenster (Breite kann abweichen)
    if im.width > GAME_W:
        x0 = (im.width - GAME_W) // 2
        im = im.crop((x0, 0, x0 + GAME_W, min(GAME_H, im.height)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path)
    return im.size


def main(argv):
    if not argv:
        print("Aufruf: python3 capture.py <name> [--look]")
        return 2
    name = argv[0]
    look = "--look" in argv[1:]

    wid = find_window()
    if not wid:
        print("FEHLER: kein Sakuna-Fenster gefunden")
        return 1

    dest = (Path("/tmp") if look else DOCS) / f"{name}.png"
    size = capture(wid, dest)
    print(f"{dest}  {size[0]}x{size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
