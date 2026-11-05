#!/usr/bin/env python3
"""Erzeugt de_rebase.py – die Zeilen-Umschluesselung fuer neue Spielstaende.

Grundidee: Die Uebersetzungstabellen sind nach (Datei, Zeilenindex) geschluesselt.
Ein Spiel-Update kann Zeilen einfügen/entfernen -> Indizes verrutschen.
Dieses Werkzeug gleicht Retail-Baum gegen den neuen Baum ab (pro Zeile:
Code + Quelltext-Spalten) und erzeugt eine Maske

    REBASE[(Pfad, "<Feld>#<NEUE Zeile>")] = alter Tabellen-Schluessel

die apply_de nur in einem Beta-/Update-Modus anwendet (Erkennung ueber
Marker-Dateien, die es nur im neuen Stand gibt). Auf dem alten Stand wird
die Maske ignoriert -> Identitaetsverhalten.

Aufruf (Beispiel; Pfade zeigen auf zuvor entpackte Baeume):

  python3 make_rebase.py \
      --pair /tmp/ret_text   /tmp/beta_text \
      --pair /tmp/ret_common /tmp/beta_common

Retail-Seite spaeter aus den Backups erzeugen:
  sakuna.py extract dataWin/Text.arc.bak-original   /tmp/ret_text
  sakuna.py extract dataWin/Common.arc.bak-original /tmp/ret_common
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sakuna as S

ROOT = Path(__file__).resolve().parent
SRC_COLS = ("English", "NameEn", "TextEn", "PostEn", "CommentEn",
            "Floor_NameEn", "Enchant_NameEn")


def rows_of(path: Path):
    data = path.read_bytes().decode("utf-8", errors="replace")
    lines = [l for l in data.split("\r") if l.strip()]
    return [l.split(",") for l in lines]


def row_keys(rows):
    hdr = rows[0]
    cols = [c for c in SRC_COLS if c in hdr]
    if not cols:
        return None, None, None
    idx = [hdr.index(c) for c in cols]
    code_i = 0
    out = []
    for r in rows[1:]:
        code = r[code_i] if len(r) > code_i else ""
        src = tuple(r[i] if len(r) > i else "" for i in idx)
        out.append((code, src))
    return out, cols, [hdr.index(c) for c in ("Spanish", "TextSp") if c in hdr]


def match_rows(old_keys, new_keys):
    """old -> (new_index|None). Stufe 1: (Code,Quelltext), Stufe 2: eindeutiger Code."""
    buckets = defaultdict(deque)
    for j, k in enumerate(new_keys):
        buckets[k].append(j)
    used = [False] * len(new_keys)
    old2new = [None] * len(old_keys)

    # Stufe 1: exakter Treffer (Code + Quelltext), Reihenfolge stabil
    for i, k in enumerate(old_keys):
        q = buckets.get(k)
        while q and used[q[0]]:
            q.popleft()
        if q:
            j = q.popleft()
            used[j] = True
            old2new[i] = j

    # Stufe 2: Code eindeutig auf beiden Seiten
    if any(v is None for v in old2new):
        old_code_cnt = defaultdict(int)
        new_code_cnt = defaultdict(int)
        for i, (code, _) in enumerate(old_keys):
            if old2new[i] is None:
                old_code_cnt[code] += 1
        for j, u in enumerate(used):
            if not u:
                new_code_cnt[new_keys[j][0]] += 1
        new_by_code = defaultdict(list)
        for j, (code, _) in enumerate(new_keys):
            if not used[j]:
                new_by_code[code].append(j)
        for i, (code, _) in enumerate(old_keys):
            if old2new[i] is not None:
                continue
            if old_code_cnt[code] == 1 and new_code_cnt[code] == 1:
                j = new_by_code[code][0]
                used[j] = True
                old2new[i] = j
    return old2new


def collect(root: Path):
    out = {}
    for dp, _d, fs in os.walk(root):
        for f in fs:
            if f.endswith(S.EXTENSIONS if hasattr(S, "EXTENSIONS") else S.CSV_EXTENSIONS):
                p = Path(dp) / f
                out[str(p.relative_to(root))] = p
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebase-Maske erzeugen")
    ap.add_argument("--pair", nargs=2, action="append", required=True,
                    metavar=("RETAIL_ROOT", "NEU_ROOT"),
                    help="zwei entpackte Baeume (alt, neu); mehrfach möglich")
    ap.add_argument("-o", "--out", default=str(ROOT / "de_rebase.py"))
    args = ap.parse_args()

    import apply_de  # Tabellen (DE) laden
    apply_de.load_tables("de")

    rels = set()
    file_rowmap = {}   # rel -> {old_row(1b): new_row(1b)|None}
    for ret_s, new_s in args.pair:
        ret, new = collect(Path(ret_s)), collect(Path(new_s))
        rels |= set(ret)
        for rel, rp in ret.items():
            np_ = new.get(rel)
            if np_ is None:
                # Datei komplett entfernt -> alle Zeilen tot
                r = rows_of(rp)
                file_rowmap[rel] = {i: None for i in range(1, len(r))}
                continue
            ok, cols, _ = row_keys(rows_of(rp))
            nk, ncols, _ = row_keys(rows_of(np_))
            if ok is None or nk is None:
                continue
            if ok == nk:
                continue  # identisch -> keine Maskierung noetig
            old2new = match_rows(ok, nk)
            rmap = {(i + 1): (j + 1 if j is not None else None)
                    for i, j in enumerate(old2new)}
            if all(k == v for k, v in rmap.items()):
                continue
            file_rowmap[rel] = rmap

    # Basename-Index (fuer alt-tabellen mit Basisnamen-Schluesseln)
    base_index = {}
    for rel in rels:
        b = os.path.splitext(os.path.basename(rel))[0]
        base_index.setdefault(b, []).append(rel)

    rebase = {}
    stats = {"neu": 0, "ident": 0, "tot": 0, "unbekannt": 0}
    for key, val in apply_de.DE.items():
        kpath, ctx = key
        # Beta-Tabellen (#beta-Suffix) duerfen niemals Teil der Maske werden -
        # sie beschreiben den neuen Stand selbst, nicht das Umschluesselungsziel.
        if isinstance(kpath, str) and kpath.endswith("#beta"):
            stats["unbekannt"] += 1
            continue
        # Vollstaendige Abdeckung: Jeder Tabellen-Schluessel bekommt einen
        # Beta-Key (Identitaetszuordnungen inklusive). Ein Beta-Key, der NICHT
        # in der Maske steht, ist damit garantiert NEUER Inhalt und darf nie
        # durch einen alten Tabellenwert befeuert werden (sonst Doppelschuss
        # wie "Option Zeile 7: neu='Large', deutsch='Standard'").
        if isinstance(kpath, str) and kpath in rels:
            rel = kpath
        elif kpath in base_index and len(base_index[kpath]) == 1:
            rel = base_index[kpath][0]
        else:
            stats["unbekannt"] += 1
            continue
        if "#" not in ctx:
            stats["unbekannt"] += 1
            continue
        field, row_s = ctx.rsplit("#", 1)
        if not row_s.isdigit():
            stats["unbekannt"] += 1
            continue
        old_row = int(row_s)
        rmap = file_rowmap.get(rel)
        new_row = rmap.get(old_row, old_row) if rmap else old_row
        if new_row is None:
            stats["tot"] += 1
            continue
        beta_key = (rel, f"{field}#{new_row}")
        # Ziel-Form = exakt der Tabellen-Schluessel (Pfad- oder Basenamen-Form)
        rebase[beta_key] = key
        stats["neu" if new_row != old_row else "ident"] += 1

    lines = [
        "# AUTO-ERZEUGT von make_rebase.py – nicht handbearbeiten!",
        "# Umschluesselung: (Datei, Feld#NEUE_Zeile) -> alter Tabellen-Schluessel.",
        "# Wird von apply_de NUR aktiviert, wenn Beta-/Update-Marker vorhanden sind.",
        "",
        "REBASE = {",
    ]
    for (p, c), tgt in sorted(rebase.items()):
        lines.append(f"    ({p!r}, {c!r}): {tgt!r},")
    lines.append("}")
    lines.append("")
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"de_rebase.py geschrieben: {len(rebase)} Zuordnungen "
          f"(umgeschluesselt={stats['neu']}, identisch={stats['ident']}, "
          f"Zeile entfallen={stats['tot']}, nicht zugeordnet={stats['unbekannt']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
