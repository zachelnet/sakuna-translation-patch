#!/usr/bin/env python3
"""Migriert alle Tabellen von Zeilen- auf Code-Schluessel (einmalig).

Vorher:  (root, "English#42")            -> Zeilenindex
Nachher: (root, "English#c:Kokorogasa")  -> Code der Quelldatei
        (root, "English#r:42")           -> nur wenn die Quellzeile KEINEN Code hat

Warum: Zeilenindizes verrutschen bei jedem Spiel-Update; Codes sind
Identitaeten. Danach sind Rebase-Maske, Beta-Marker und #beta-Suffix ueberfluessig.

Aufruf:
  python3 migrate_keys.py --retail-text /tmp/ret_text --retail-common /tmp/ret_common \
      --beta-text  <pristine>/Text --beta-common <pristine>/Common            # Trockenlauf
  ... mit --write zum Umschreiben der Tabellen in tables/de/[beta/]

Trockenlauf prueft pro Eintrag: Quelldatei, Zeilenexistenz, Code lesbar, keine
Wertekollisionen. Erst danach --write; nach dem Schreiben werden alle Altwerte
gegen die neu geladenen Tabellen gegengeprueft.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sakuna as S

RETAIL_DIR = HERE / "tables" / "de"
BETA_DIR = HERE / "tables" / "de" / "beta"


def load_module(path: Path, qual: str):
    spec = importlib.util.spec_from_file_location(qual, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tuple_dicts(mod) -> dict:
    out = {}
    for attr, val in vars(mod).items():
        if not isinstance(val, dict) or not val:
            continue
        if not all(
            isinstance(k, tuple) and len(k) == 2
            and isinstance(k[0], str) and isinstance(k[1], str)
            for k in val
        ):
            continue
        out[attr] = val
    return out


def po_basename_map() -> dict:
    m = defaultdict(set)
    for root in ("po", "poCommon"):
        for dp, _d, fs in os.walk(HERE / root):
            for f in fs:
                if f.endswith(".po"):
                    h, _e = S.parse_po(os.path.join(dp, f))
                    rel = h.get("Sakuna-File", "")
                    if rel:
                        m[os.path.splitext(os.path.basename(rel))[0]].add(rel)
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description="Tabellen auf Code-Schluessel migrieren")
    ap.add_argument("--retail-text", required=True)
    ap.add_argument("--retail-common", required=True)
    ap.add_argument("--beta-text", required=True)
    ap.add_argument("--beta-common", required=True)
    ap.add_argument("--write", action="store_true", help="Dateien tatsaechlich umschreiben")
    args = ap.parse_args()

    retail_roots = [Path(args.retail_text), Path(args.retail_common)]
    beta_roots = [Path(args.beta_text), Path(args.beta_common)]
    b2r = po_basename_map()
    rows_cache: dict = {}
    code_counts: dict = {}

    def get_rows(rel: str, roots):
        key = (rel, str(roots[0]))
        if key not in rows_cache:
            src = None
            for r in roots:
                if (r / rel).is_file():
                    src = r / rel
                    break
            if src is None:
                return None
            data = src.read_bytes().decode("utf-8", errors="replace")
            rows_cache[key] = [l.split(",") for l in data.split("\r")]
        return rows_cache[key]

    fatal = []
    notes = []
    plan: dict[Path, dict[str, dict]] = {}   # path -> {dictname: {newkey: val}}
    n_c = n_r = collapses = 0

    for group, roots, dirs in (
        ("retail", retail_roots, [RETAIL_DIR]),
        ("beta", beta_roots, [BETA_DIR]),
    ):
        for d in dirs:
            for path in sorted(d.glob("*.py")):
                mod = load_module(path, f"mig_{group}_{path.stem}")
                dicts = tuple_dicts(mod)
                per_file: dict[str, dict] = {}
                for dname, dct in dicts.items():
                    newd = {}
                    for (root, ctx), val in dct.items():
                        if "#" not in ctx:
                            fatal.append(f"{path.name}: ctx ohne '#': {ctx!r}")
                            continue
                        field, row_s = ctx.rsplit("#", 1)
                        if not row_s.isdigit():
                            fatal.append(f"{path.name}: kein Zeilenindex: {ctx!r}")
                            continue
                        row = int(row_s)
                        is_beta = root.endswith("#beta")
                        bare = root[:-5] if is_beta else root
                        if "/" in bare:
                            rel = bare
                        else:
                            cands = b2r.get(bare, set())
                            if len(cands) == 1:
                                rel = next(iter(cands))
                            elif not cands:
                                fatal.append(f"{path.name}: kein PO fuer Basenamen {bare!r}")
                                continue
                            else:
                                hits = []
                                for c in sorted(cands):
                                    for r in roots:
                                        p = r / c
                                        if p.is_file():
                                            hdr = p.read_bytes().decode(
                                                "utf-8", errors="replace"
                                            ).split("\r", 1)[0].split(",")
                                            if field in hdr:
                                                hits.append(c)
                                                break
                                if len(hits) == 1:
                                    rel = hits[0]
                                else:
                                    fatal.append(
                                        f"{path.name}: Basenamen {bare!r} mehrdeutig "
                                        f"fuer Feld {field!r} (Treffer: {hits})"
                                    )
                                    continue
                        rows = get_rows(rel, roots)
                        if rows is None:
                            fatal.append(f"{path.name}: Quelldatei fehlt: {rel}")
                            continue
                        if row >= len(rows):
                            fatal.append(
                                f"{path.name}: {rel} Zeile {row} existiert nicht "
                                f"(nur {len(rows) - 1})"
                            )
                            continue
                        code = rows[row][0]
                        # Nur EINDEUTIGE Codes schuetzen vor Zeilenverschiebungen.
                        # Leere oder dateiweit konstante Codes (z.B. Travel: Bg-
                        # Spalte in jeder Zeile gleich) bleiben Zeilen-Keys (r:),
                        # exakt die Robustheit des bisherigen Standes.
                        uniq = None
                        if code:
                            cnt = code_counts.get((rel, str(roots[0])))
                            if cnt is None:
                                cnt = {}
                                for i in range(1, len(rows)):
                                    if rows[i]:
                                        cnt[rows[i][0]] = cnt.get(rows[i][0], 0) + 1
                                code_counts[(rel, str(roots[0]))] = cnt
                            uniq = cnt.get(code, 0) == 1
                        new_ctx = (
                            f"{field}#c:{code}" if uniq else f"{field}#r:{row}"
                        )
                        # "#beta"-Root bleibt erhalten (Stand-abhaengige
                        # Werte wie Credits+KING koexistieren mit Retail).
                        key = (root, new_ctx)
                        if key in newd:
                            if newd[key] == val:
                                collapses += 1
                                notes.append(f"{path.name}: {key!r} identisch zusammengelegt")
                            else:
                                fatal.append(
                                    f"{path.name}: Kollision {key!r} mit unterschiedlichen Werten"
                                )
                            continue
                        newd[key] = val
                        if uniq:
                            n_c += 1
                        else:
                            n_r += 1
                    per_file[dname] = newd
                plan[path] = per_file

    if fatal:
        print(f"FEHLER ({len(fatal)}):")
        for f in fatal[:40]:
            print("  ", f)
        if len(fatal) > 40:
            print(f"   ... +{len(fatal) - 40}")
        return 1

    old_total = 0
    for path, per_file in plan.items():
        mod = load_module(path, f"cnt_{path.stem}")
        old_total += sum(len(d) for d in tuple_dicts(mod).values())
    print(
        f"Trockenlauf OK: {old_total} Eintraege -> {sum(len(v) for pf in plan.values() for v in pf.values())} "
        f"Keys (c-Form: {n_c}, r-Form: {n_r}, Zusammenlegungen: {collapses})"
    )
    for n in notes[:10]:
        print("  note:", n)
    if not args.write:
        print("Kein --write: Dateien unveraendert.")
        return 0

    # Altwerte VOR dem Schreiben sichern (frisches Laden von der Platte)
    import apply_de as A
    pre = dict(A.load_tables("de"))

    for path, per_file in plan.items():
        lines = [
            "# AUTO-MIGRIERT auf Code-Schluessel (migrate_keys.py).",
            '# Keys: (pfad_oder_basename, "Feld#c:CODE") bzw. "Feld#r:ZEILE" (Quellzeile ohne Code).',
            "",
        ]
        for dname, newd in per_file.items():
            lines.append(f"{dname} = {{")
            for (rk, ck), v in sorted(newd.items(), key=lambda kv: kv[0]):
                lines.append(f"    ({rk!r}, {ck!r}): {v!r},")
            lines.append("}")
            lines.append("")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(plan)} Tabellendateien geschrieben.")

    # Nachpruefung: alle Altwerte weiterhin auffindbar (Schluessel-Mapping oben)
    #   Rekonstruktion: erneut migrieren und gegen post-DE pruefen.
    post = dict(A.load_tables("de"))
    # Mapping aus frischem Plan (Identische Logik; Dateien sind bereits neu -
    #   Alt-Keys gibt es nicht mehr). Stattdessen: Wertemultiset-Vergleich.
    pre_vals = sorted(map(repr, pre.values()))
    post_vals = sorted(map(repr, post.values()))
    if pre_vals != post_vals:
        print("FEHLER: Wertemultiset vor/nach der Migration unterscheidet sich!")
        only_pre = [v for v in pre_vals if post_vals.count(v) != pre_vals.count(v)]
        for v in set(only_pre[:10]):
            print("   fehlt/nur alt:", v[:120])
        return 1
    print(f"Nachpruefung OK: {len(pre)} Alt-Werte == {len(post)} Neu-Werte (identisches Multiset).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
