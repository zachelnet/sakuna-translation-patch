#!/usr/bin/env python3
"""SakunaDeutsch – automatisierter Installer/Builder (Windows, Linux, macOS).

Was das Skript macht:
  1. Sucht die Spielinstallation (Steam-Bibliotheken, Proton, Env-Var,
     oder --game-dir). Unter Windows findet es die Registry-Pfade,
     unter Linux die ueblichen steamapps-Locations inkl. Flatpak.
  2. Installiert fehlende Python-Abhaengigkeiten (nur `lz4`).
  3. Legt dataWin/*.arc.bak-original an (einmalig, wird nie ueberschrieben).
  4. Baut den deutschen Patch aus DEINER eigenen Spielspiegelung:
     extract -> po-dir -> apply_de -> unpo-dir -> validate -> pack.
  5. Kopiert die fertigen Pakete ins Spiel und setzt "Language": "Sp".

Mit --restore werden die Originaldateien aus den Backups zurueckkopiert.

Aufrufe:
  python install.py                 # bauen + installieren
  python install.py --restore       # auf Retail zuruecksetzen
  python install.py --game-dir "Pfad/zum/Spiel"
  python install.py --yes           # ohne Rueckfrage
  SAKUNA_DIR="Pfad" python install.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAME_DIRNAME = "Sakuna Of Rice and Ruin"
BACKUP_SUFFIX = ".bak-original"
BUILD_DIRS = ("work", "mod", "po", "poCommon")


def info(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"!!  {msg}", flush=True)


def die(msg: str) -> None:
    print(f"FEHLER: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def run(args: list[str], cwd: Path = ROOT) -> int:
    """Fuehrt ein Kommando mit diesem Python aus, gibt Exit-Code zurueck."""
    cmd = [sys.executable, *args]
    r = subprocess.run(cmd, cwd=str(cwd))
    return r.returncode


def sha16(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Spielpfad finden
# --------------------------------------------------------------------------- #

def _vdf_library_paths(vdf: Path) -> list[Path]:
    """Liest libraryfolders.vdf (alt und neu) und liefert steamapps-Ordner."""
    try:
        text = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    raw = re.findall(r'"(?:path|\d+)"\s*"([^"]+)"', text)
    out = []
    for p in raw:
        p = p.replace("\\\\", "\\")
        out.append(Path(p) / "steamapps")
    return out


def _looks_like_game(d: Path) -> bool:
    return (d / "dataWin" / "Text.arc").is_file() and (d / "dataWin" / "Common.arc").is_file()


def find_game(explicit: str | None) -> Path | None:
    cands: list[Path] = []

    if explicit:
        cands.append(Path(explicit).expanduser())
    if os.environ.get("SAKUNA_DIR"):
        cands.append(Path(os.environ["SAKUNA_DIR"]).expanduser())

    # Direkt im Repo/Arbeitsverzeichnis?
    for base in (Path.cwd(), ROOT):
        cands.append(base)
        cands.append(base / GAME_DIRNAME)
        cands.append(base.parent / GAME_DIRNAME)

    # Steam-Wurzeln je Plattform
    roots: list[Path] = []
    if sys.platform == "win32":
        for var in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(var)
            if base:
                roots.append(Path(base) / "Steam")
        try:  # optional: Registry
            import winreg  # type: ignore

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
            ) as key:
                val, _ = winreg.QueryValueEx(key, "SteamPath")
                if val:
                    roots.append(Path(val))
        except Exception:
            pass
    else:
        home = Path.home()
        roots += [
            home / ".steam" / "steam",
            home / ".steam" / "root",
            home / ".steam" / "debian-installation",
            home / ".local" / "share" / "Steam",
            home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        ]

    steamapps: list[Path] = []
    for root in roots:
        sa = root / "steamapps"
        if sa.is_dir():
            steamapps.append(sa)
            steamapps += _vdf_library_paths(sa / "libraryfolders.vdf")

    seen: set[Path] = set()
    for sa in steamapps:
        if sa in seen:
            continue
        seen.add(sa)
        cands.append(sa / "common" / GAME_DIRNAME)

    for c in cands:
        try:
            if _looks_like_game(c):
                return c.resolve()
        except OSError:
            continue
    return None


# --------------------------------------------------------------------------- #
# Pristine-Quellen: Der Bau darf NIE aus der eigenen letzten Ausgabe erfolgen
# (sonst ueberlebt ein Fehlschreib die naechste Runde in der Quellspalte).
# Stattdessen wird der jeweils EXTERNE Eingang (Steam/Backup) als frischer
# Extrakt gesichert; eigene Ausgaben werden ignoriert.
# --------------------------------------------------------------------------- #

PRISTINE_DIR = ".sakunadeutsch_pristine"


def pristine_sources(game: Path) -> tuple[Path, Path]:
    dw = game / "dataWin"
    out: list[Path] = []
    for name, sub in (("Text.arc", "Text"), ("Common.arc", "Common")):
        inp = dw / name
        our = ROOT / name.replace(".arc", ".mod.arc")
        pr = dw / PRISTINE_DIR / sub
        external = (not our.exists()) or (sha16(inp) != sha16(our))
        if external or not (pr / "manifest.json").exists():
            shutil.rmtree(pr, ignore_errors=True)
            pr.parent.mkdir(parents=True, exist_ok=True)
            why = "externe Version (Steam/Update/Wechsel)" if external else "Fallback"
            info(f"{name}: pristine sichern ({why})")
            if run(["sakuna.py", "extract", str(inp), str(pr)]) != 0:
                die(f"pristine-Extrakt von {name} fehlgeschlagen")
        out.append(pr)
    return out[0], out[1]


# --------------------------------------------------------------------------- #
# Abhaengigkeiten
# --------------------------------------------------------------------------- #

def ensure_lz4(yes: bool) -> None:
    try:
        importlib.import_module("lz4.block")
        return
    except ImportError:
        pass
    if not yes:
        ans = input("Fehlendes Paket 'lz4' installieren? pip wird ausgefuehrt. [J/n] ")
        if ans.strip().lower() in ("n", "no"):
            die("Ohne 'lz4' kann nicht gebaut werden: pip install lz4")
    info("Installiere Abhaengigkeit: lz4")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "lz4"])
    if r.returncode != 0:
        die(
            "pip install lz4 ist fehlgeschlagen. Bitte manuell ausfuehren "
            "(ggf. mit --user oder in einer venv) und das Skript erneut starten."
        )
    try:
        importlib.import_module("lz4.block")
    except ImportError:
        die("lz4 ist installiert, importiert aber nicht. PATH/venv pruefen.")


# --------------------------------------------------------------------------- #
# Backup / Restore / Sprache
# --------------------------------------------------------------------------- #

def backup_archives(game: Path) -> None:
    for name in ("Text.arc", "Common.arc"):
        src = game / "dataWin" / name
        bak = game / "dataWin" / (name + BACKUP_SUFFIX)
        if not src.is_file():
            die(f"fehlt: {src}")
        if bak.exists():
            info(f"Backup vorhanden (bleibt unveraendert): {bak.name}")
        else:
            shutil.copy2(src, bak)
            info(f"Backup angelegt: {bak.name}")


def restore_archives(game: Path) -> None:
    any_done = False
    for name in ("Text.arc", "Common.arc"):
        bak = game / "dataWin" / (name + BACKUP_SUFFIX)
        dst = game / "dataWin" / name
        if not bak.exists():
            warn(f"kein Backup gefunden: {bak.name} – uebersprungen")
            continue
        shutil.copy2(bak, dst)
        info(f"wiederhergestellt: {name} ({sha16(dst)})")
        any_done = True
    if not any_done:
        die("keine Backups vorhanden – nichts wiederhergestellt")
    info("Fertig. Retail ist zurueck. Sprache in TaueConfig.json bei Bedarf manuell aendern.")


def set_language(game: Path, lang: str) -> None:
    cfg = game / "TaueConfig.json"
    if not cfg.is_file():
        warn(f"{cfg.name} nicht gefunden – Sprache nicht geaendert")
        return
    try:
        text = cfg.read_text(encoding="utf-8-sig")
    except OSError as exc:
        warn(f"{cfg.name} nicht lesbar: {exc}")
        return
    new, n = re.subn(
        r'("Language"\s*:\s*)"[^"]*"', rf'\1"{lang}"', text, count=1
    )
    if n == 0:
        warn(f'kein "Language"-Schluessel in {cfg.name} gefunden – bitte manuell setzen')
        return
    cfg.write_text(new, encoding="utf-8")
    info(f'{cfg.name}: Language = "{lang}"')


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #

def build(game: Path, text_src: Path, common_src: Path) -> None:
    # Alte Artefakte weg – werden sofort frisch neu aufgebaut (beide Baeume).
    for d in BUILD_DIRS:
        shutil.rmtree(ROOT / d, ignore_errors=True)

    info("Schritt 1/6: Archivquellen bereitstellen (pristine)")
    shutil.copytree(text_src, ROOT / "work" / "Text")
    shutil.copytree(common_src, ROOT / "work" / "Common")

    # Spielstand-Kompatitaet: Update/Beta erkennen, wenn keine Maske hinterlegt
    beta_hit = (
        (ROOT / "work/Text/Text/Event/Miyako/Kamuhitsuki.csvtxt").exists()
        or (ROOT / "work/Common/Param/Game/EventStarter.csv").exists()
    )
    if beta_hit and not (ROOT / "de_rebase.py").exists():
        die(
            "Dieser Spielstand (Update/Beta) hat geaenderte Zeilen, aber\n"
            "        de_rebase.py fehlt. Ein normaler Lauf wuerde Zeilen falsch\n"
            "        zuordnen. Maske mit make_rebase.py erzeugen und erneut starten."
        )
    if beta_hit:
        info("Update-/Beta-Stand erkannt - Rebase-Maske wird verwendet")

    info("Schritt 2/6: PO-Dateien erzeugen (msgids aus deiner Kopie)")
    if run(["sakuna.py", "po-dir", "work/Text", "po"]) != 0:
        die("po-dir Text fehlgeschlagen")
    if run(["sakuna.py", "po-dir", "work/Common", "poCommon"]) != 0:
        die("po-dir Common fehlgeschlagen")

    info("Schritt 3/6: deutsche Tabellen einspielen (apply_de)")
    for root in ("po", "poCommon"):
        rc = run(["apply_de.py", root])
        if rc not in (0, 1):
            die(f"apply_de {root} fehlgeschlagen (Exit {rc})")
        if rc == 1:
            warn(f"apply_de {root}: einige Eintraege ohne Tabellen-Eintrag – diese Zeilen bleiben original")

    info("Schritt 4/6: Uebersetzungen zurueck in die CSVs schreiben")
    if run(["sakuna.py", "unpo-dir", "po", "work/Text", "mod/Text"]) != 0:
        die("unpo-dir Text fehlgeschlagen")
    if run(["sakuna.py", "unpo-dir", "poCommon", "work/Common", "mod/Common"]) != 0:
        die("unpo-dir Common fehlgeschlagen")

    info("Schritt 5/6: validieren")
    if run(["sakuna.py", "validate-dir", "mod/Text", "--src", "English", "--dst", "Spanish"]) != 0:
        die("validate-dir Text meldet Fehler – Installation abgebrochen")

    info("Schritt 6/6: packen")
    if run(["sakuna.py", "pack", "mod/Text", "Text.mod.arc"]) != 0:
        die("pack Text fehlgeschlagen")
    if run(["sakuna.py", "pack", "mod/Common", "Common.mod.arc"]) != 0:
        die("pack Common fehlgeschlagen")


def main() -> int:
    if sys.version_info < (3, 10):
        die("Python 3.10+ benoetigt (aktuell: %s)" % sys.version.split()[0])

    ap = argparse.ArgumentParser(description="SakunaDeutsch – deutscher Sprachpatch, automatisiert")
    ap.add_argument("--game-dir", help="Pfad zum Spielverzeichnis (enthält dataWin/)")
    ap.add_argument("--restore", action="store_true", help="Originaldateien aus Backups wiederherstellen")
    ap.add_argument("--yes", action="store_true", help="keine Rueckfragen")
    ap.add_argument("--keep-language", action="store_true", help="TaueConfig.json nicht anfassen")
    ap.add_argument("--language", default="Sp", help="Sprachcode (Standard: Sp)")
    args = ap.parse_args()

    game = find_game(args.game_dir)
    if game is None:
        die(
            "Spielinstallation nicht gefunden.\n"
            "  Loesung 1: --game-dir \"Pfad/zum/Sakuna Of Rice and Ruin\"\n"
            "  Loesung 2: Umgebungsvariable SAKUNA_DIR auf den Ordner setzen\n"
            "  (der Ordner muss dataWin/Text.arc enthalten)"
        )
    info(f"Spiel gefunden: {game}")

    if args.restore:
        if not args.yes:
            ans = input("Original wiederherstellen? Backups werden eingespielt. [J/n] ")
            if ans.strip().lower() in ("n", "no"):
                print("abgebrochen")
                return 0
        restore_archives(game)
        return 0

    if not args.yes:
        ans = input(
            "Deutschen Patch bauen und installieren? "
            "(Original wird zuvor gesichert) [J/n] "
        )
        if ans.strip().lower() in ("n", "no"):
            print("abgebrochen")
            return 0

    ensure_lz4(args.yes)
    backup_archives(game)
    text_src, common_src = pristine_sources(game)
    build(game, text_src, common_src)

    info("Installiere gebaute Pakete")
    for name in ("Text.arc", "Common.arc"):
        src = ROOT / (name.replace(".arc", ".mod.arc"))
        if not src.is_file():
            die(f"gebautes Paket fehlt: {src.name}")
        shutil.copy2(src, game / "dataWin" / name)
        info(f"{name} = {sha16(game / 'dataWin' / name)}")

    if not args.keep_language:
        set_language(game, args.language)

    print()
    info("FERTIG. Spiel starten – Texte erscheinen auf Deutsch.")
    info("Zurueck zum Original:  python install.py --restore")
    return 0


if __name__ == "__main__":
    sys.exit(main())
