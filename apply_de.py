#!/usr/bin/env python3
"""Trägt alle deutschen Strings in alle .po-Dateien unter po/ ein.

Lookup pro Eintrag:
  1. (voller Archivpfad, msgctxt)   - fuer Dateien mit doppeltem Namen
  2. (Dateiname ohne Endung, msgctxt) - fuer die aelten Tabellen

Fehlt beides, wird der Eintrag unveraendert gelassen und gemeldet.
"""

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "tables"))        # Retail-Tabellen
sys.path.insert(0, os.path.join(_HERE, "tables", "beta"))  # nur-Beta-Tabellen
import sakuna as S
import glob as _glob
import importlib.util as _ilu


def load_tables(lang: str = "de") -> dict:
    """Laedt alle Tabellen aus tables/<lang>/ und tables/<lang>/beta/.

    Jede .py-Datei darf ein oder mehrere Dicts mit 2-Tuple-Keys
    ((pfad_oder_basename, "Feld#...") -> Wert) definieren. Hilfsdaten
    (_FILES & Co.) mit Nicht-Tuple-Keys werden ignoriert. Neu hinzufuegen
    heisst: Datei ablegen - kein weiteres Registration noetig.
    """
    global DE
    DE = {}
    base = os.path.join(_HERE, "tables", lang)
    for d in (base, os.path.join(base, "beta")):
        if not os.path.isdir(d):
            if d != os.path.join(base, "beta"):
                raise SystemExit(f"Tabellenverzeichnis fehlt: {d}")
            continue
        for path in sorted(_glob.glob(os.path.join(d, "*.py"))):
            name = os.path.splitext(os.path.basename(path))[0]
            qual = f"sakuna_tbl_{lang}_{os.path.basename(os.path.dirname(d))}_{name}"
            spec = _ilu.spec_from_file_location(qual, path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for attr, val in vars(mod).items():
                if not isinstance(val, dict) or not val:
                    continue
                if not all(
                    isinstance(k, tuple) and len(k) == 2
                    and isinstance(k[0], str) and isinstance(k[1], str)
                    for k in val
                ):
                    continue
                for k, v in val.items():
                    if k in DE and DE[k] != v:
                        print(f"WARNUNG: doppelter Tabellen-Schluessel, Wert wird ueberschrieben: {k!r}")
                    DE[k] = v
    return DE


DE = {}

# --------------------------------------------------------------------------- #
# Rebase (Update-/Beta-Spielstaende): apply_de merkt sich (Datei, Feld#NEUE
# Zeile) -> (alter Tabellen-Schluessel). Nur aktiv, wenn Marker-Dateien
# vorhanden sind, die es ausschliesslich im neuen Stand gibt; auf dem alten
# Stand wird die Maske ignoriert (Identitaet).
# --------------------------------------------------------------------------- #

REBASE = {}
try:
    from de_rebase import REBASE as _REBASE
    REBASE = _REBASE
except ImportError:
    pass

BETA_MARKERS = (
    "Text/Event/Miyako/Kamuhitsuki.po",   # nur im Beta-/Update-Stand vorhanden
    "Param/Game/EventStarter.po",         # dito in Common (falls PO existiert)
    # Werkbaum-Abdeckung (gilt fuer beide Wurzeln): die beiden Marker-Dateien
    # existieren ausschliesslich im neuen Spielstand - auch ohne dass ihre
    # POs erzeugt wurden (EventStarter.csv hat z.B. keine Quellspalte).
    os.path.join("work", "Text", "Text", "Event", "Miyako", "Kamuhitsuki.csvtxt"),
    os.path.join("work", "Common", "Param", "Game", "EventStarter.csv"),
)


def _beta_active(po_root: str) -> bool:
    # Relative Marker gegen po_root, absolute/relativ-zu-cwd Marker roh pruefen
    for m in BETA_MARKERS:
        if os.path.exists(m):
            return True
        if os.path.exists(os.path.join(po_root, m)):
            return True
    return False


_UNSET = object()   # noch nicht entschieden
_MISSING = object() # kein Tabelleneintrag -> missing-Report


def write_po(path, header, entries):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('msgid ""\nmsgstr ""\n')
        for k, v in header.items():
            fh.write(f'"{k}: {S._po_escape(v)}\\n"\n')
        fh.write("\n")
        for e in entries:
            # Code-Kommentar mitschreiben (Grundlage der Code-Lookups in
            # parse_po; csv_to_po erzeugt das gleiche Format).
            ctx = e["msgctxt"]
            code = e.get("code")
            if code is not None and "#" in ctx:
                field, row = ctx.rsplit("#", 1)
                fh.write(f"#: row:{row} code:{code} field:{field}\n")
            fh.write(f'msgctxt "{S._po_escape(ctx)}"\n')
            fh.write(f'msgid "{S._po_escape(e["msgid"])}"\n')
            fh.write(f'msgstr "{S._po_escape(e["msgstr"])}"\n\n')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="apply_de.py",
        description="Traegt alle Uebersetzungen in die .po-Dateien eines PO-Wurzelverzeichnisses ein.",
    )
    ap.add_argument("po_root", nargs="?", default="po",
                    help="PO-Wurzelverzeichnis (Standard: po)")
    ap.add_argument("--lang", default="de",
                    help="Sprachverzeichnis unter tables/ (Standard: de)")
    args = ap.parse_args(argv)
    load_tables(args.lang)
    po_root = args.po_root
    filled = 0
    missing = []
    checked = 0
    active = False
    if _beta_active(po_root):
        if not REBASE:
            print(
                "FEHLER: Spielstand mit geaenderten Zeilen erkannt (Update/Beta),\n"
                "        aber de_rebase.py fehlt oder ist leer. Ohne Maske waeren\n"
                "        Zeilen falsch zugeordnet - abgebrochen.\n"
                "        Neuen Stand mit make_rebase.py abdecken."
            )
            return 2
        active = True
        print(f"Update-/Beta-Stand erkannt - Rebase aktiv: {len(REBASE)} Zuordnungen.")
    # Alle Dateien, fuer die im aktiven Modus NUR Beta-Key/Rebase gilt
    # (REBASE-Ziele + "#beta"-Tabellen). Alles andere darf klassisch greifen.
    masked_rels = set()
    if active:
        masked_rels = {k[0] for k in REBASE} | {
            k[0][: -len("#beta")]
            for k in DE
            if isinstance(k[0], str) and k[0].endswith("#beta")
        }
    for dirpath, _dirs, files in os.walk(po_root):
        for fn in sorted(files):
            if not fn.endswith(".po"):
                continue
            po_path = os.path.join(dirpath, fn)
            header, entries = S.parse_po(po_path)
            archive_path = header.get("Sakuna-File", "")
            if not archive_path:
                print(f"  WARNUNG {po_path}: kein Sakuna-File im Header")
                continue
            base = os.path.splitext(os.path.basename(archive_path))[0]
            checked += 1
            for e in entries:
                key_path = (archive_path, e["msgctxt"])
                key_base = (base, e["msgctxt"])
                val = _UNSET
                if active:
                    # 1) Beta-eigener Eintrag (gewinnt auch ueber Rebase)
                    bk = (archive_path + "#beta", e["msgctxt"])
                    if bk in DE:
                        val = DE[bk]
                    else:
                        # 2) Zeilen-Umschluesselung der Maske
                        nk = REBASE.get(key_path)
                        if nk is not None:
                            val = DE.get(nk, _MISSING)
                        # 3) maskierte Datei, Key unbekannt -> neuer Inhalt
                        elif archive_path in masked_rels:
                            val = _MISSING
                if val is _UNSET:
                    # 4) klassischer Fallback (Retail/Identitaet)
                    if key_path in DE:
                        val = DE[key_path]
                    elif key_base in DE:
                        val = DE[key_base]
                    else:
                        val = _MISSING
                if val is _MISSING:
                    missing.append((archive_path, e["msgctxt"], e["msgid"]))
                    continue
                if val is None:
                    continue
                e["msgstr"] = val
                filled += 1
            write_po(po_path, header, entries)

    print(f"{filled} Uebersetzungen eingetragen in {checked} PO-Dateien.")
    if missing:
        print(f"{len(missing)} Eintraege ohne Eintrag (bleiben Original):")
        for path, ctx, mid in missing[:60]:
            print(f"   {path} [{ctx}] {mid[:70]!r}")
        if len(missing) > 60:
            print(f"   ... {len(missing) - 60} weitere")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
