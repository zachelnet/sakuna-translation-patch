#!/usr/bin/env python3
"""Verifiziert den Build gegen die Tabellen (Beta- und Retail-Modus).

Fuer jeden gefuellten PO-Eintrag wird wie in apply_de aufgeloest:
  1. DE[(Pfad + "#beta", ctx)]          Beta-eigener Eintrag
  2. REBASE[(Pfad, ctx)] -> DE[ziel]    Zeilen-Umschluesselung
  3. Datei maskiert, nichts gefunden    -> Fehler (unzulaessiger Wert)
  4. klassischer Fallback               Retail/Identitaet

Geprueft wird:
  a) msgstr == Tabellenwert
  b) CSV-Zelle == msgstr (Komma -> \\1)
  c) msgid    == Quellzelle der CSV (faengt Zeilenindex-Drift)

Ausgabe: "verifiziert N | Mismatch 0" ; Exit 1 bei Mismatch.
Zusaetzlich (nur Information): leere msgstr, die auf einen Tabellenwert
zeigen (nicht eingespielt), und leere, die absichtlich None sind.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sakuna as S
import apply_de as A
try:
    import de_rebase as R
    REBASE = R.REBASE
except ImportError:
    REBASE = {}

SENT = object()    # noch nicht entschieden -> Stufe 4 (klassischer Fallback)
MISS = object()    # Terminal: kein Tabellenziel (fehlt/offen), kein Fallback

ROOTS = (("po", "mod/Text"), ("poCommon", "mod/Common"))


def main() -> int:
    lang = "de"
    argv = sys.argv[1:]
    if "--lang" in argv:
        lang = argv[argv.index("--lang") + 1]
    A.load_tables(lang)
    active = any(A._beta_active(root) for root, _ in ROOTS)
    masked_rels = set()
    if active and REBASE:
        masked_rels = {k[0] for k in REBASE} | {
            k[0][: -len("#beta")]
            for k in A.DE
            if isinstance(k[0], str) and k[0].endswith("#beta")
        }
    checked = mismatch = open_work = intentional = 0
    for po_root, mod_root in ROOTS:
        for dirpath, _dirs, files in os.walk(po_root):
            for fn in sorted(files):
                if not fn.endswith(".po"):
                    continue
                h, entries = S.parse_po(os.path.join(dirpath, fn))
                rel = h.get("Sakuna-File", "")
                if not rel:
                    continue
                base = os.path.splitext(os.path.basename(rel))[0]
                srcs = [x for x in h.get("Sakuna-Src", "").split(",") if x]
                dsts = [x for x in h.get("Sakuna-Dst", "").split(",") if x]
                dmap = dict(zip(srcs, dsts))
                csv_path = os.path.join(mod_root, rel)
                if not os.path.exists(csv_path):
                    mismatch += 1
                    print(f"  FEHLER {rel}: CSV fehlt in {mod_root}")
                    continue
                rows = open(csv_path, "rb").read().decode("utf-8", errors="replace").split("\r")
                hdr = rows[0].split(",")

                for e in entries:
                    ctx = e["msgctxt"]
                    key_path = (rel, ctx)
                    key_base = (base, ctx)
                    val = SENT
                    if active and REBASE:
                        bk = (rel + "#beta", ctx)
                        if bk in A.DE:
                            val = A.DE[bk]
                        else:
                            nk = REBASE.get(key_path)
                            if nk is not None:
                                val = A.DE.get(nk, MISS)
                            elif rel in masked_rels:
                                val = MISS   # Terminal, kein Fallback
                    if val is SENT:
                        if key_path in A.DE:
                            val = A.DE[key_path]
                        elif key_base in A.DE:
                            val = A.DE[key_base]
                        else:
                            val = MISS
                    # Aufloesungs-Ergebnis klassifizieren
                    if val is MISS:
                        if e["msgstr"]:
                            mismatch += 1
                            print(f"  FEHLER {rel} [{ctx}]: msgstr vorhanden, "
                                  f"aber kein Tabellenziel")
                        else:
                            open_work += 1
                        continue
                    if val is None:
                        if e["msgstr"]:
                            mismatch += 1
                            print(f"  FEHLER {rel} [{ctx}]: None-Tabelle, aber msgstr gesetzt")
                        else:
                            intentional += 1
                        continue
                    if not e["msgstr"]:
                        open_work += 1
                        continue
                    # a) msgstr == Tabellenwert
                    if e["msgstr"] != val:
                        mismatch += 1
                        print(f"  FEHLER {rel} [{ctx}]: msgstr != Tabelle "
                              f"({e['msgstr'][:36]!r} vs {val[:36]!r})")
                        continue
                    # b) Zelle == msgstr (Komma -> \1)
                    fld, row_s = ctx.rsplit("#", 1)
                    if not row_s.isdigit() or int(row_s) >= len(rows):
                        mismatch += 1
                        print(f"  FEHLER {rel} [{ctx}]: Zeile ausserhalb der CSV")
                        continue
                    if fld not in dmap or fld not in hdr:
                        mismatch += 1
                        print(f"  FEHLER {rel} [{ctx}]: Spalte fehlt")
                        continue
                    cell_row = rows[int(row_s)].split(",")
                    ci = hdr.index(dmap[fld])
                    if len(cell_row) <= ci:
                        mismatch += 1
                        print(f"  FEHLER {rel} [{ctx}]: Zelle zu kurz")
                        continue
                    if cell_row[ci] != e["msgstr"].replace(",", "\\1"):
                        mismatch += 1
                        print(f"  FEHLER {rel} [{ctx}]: Zelle != msgstr "
                              f"({cell_row[ci][:36]!r})")
                        continue
                    # c) msgid == Quellzelle (Drift-Check)
                    si = hdr.index(fld) if fld in hdr else None
                    if si is not None:
                        want = e["msgid"].replace(",", "\\1")
                        if cell_row[si] != want:
                            mismatch += 1
                            print(f"  FEHLER {rel} [{ctx}]: msgid != Quellzelle "
                                  f"(Zeilenindex-Drift?) {cell_row[si][:40]!r} vs {want[:40]!r}")
                            continue
                    checked += 1

    mode = "Beta/aktiv" if (active and REBASE) else "Retail/inaktiv"
    print(f"[{mode}] verifiziert: {checked} | Mismatch: {mismatch} | "
          f"offen (noch nicht uebersetzt): {open_work} | absichtlich None: {intentional}")
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
