#!/usr/bin/env python3
"""Sakuna: Of Rice and Ruin - Archiv- und Uebersetzungswerkzeug (Python-Port).

Basiert auf der Idee von Kaplas80/SakunaTools (MIT), aber:
  * Spalten waehlbar (Quelle/Ziel, z.B. English -> Spanish)
  * Uebersetzung wird in die ZIELspalte geschrieben, die Quellspalte bleibt
  * Werkzeug prueft Markup- und Laengen-Konsistenz

Kommanden:
  extract    ARC -> Verzeichnis (+ manifest.json)
  pack       Verzeichnis -> ARC (LZ4, Standard)
  to-po      eine CSV-Datei -> .po          (msgid = Quellspalte)
  from-po    .po + Original-CSV -> neue CSV (msgstr -> Zielspalte)
  po-dir     alles unter einem Ordner nach .po
  unpo-dir   alle .po auf eine CSV-Baum zurueckspielen
  validate   Markup-/Laengen-Pruefung einer uebersetzten CSV

Beispiel (Spanisch durch Deutsch ersetzen):
  sakuna.py extract dataWin/Text.arc   work/Text
  sakuna.py po-dir  work/Text          po/Text --src English --dst Spanish
  # .po-Dateien uebersetzen (msgid=Englisch, msgstr=Deutsch)
  sakuna.py unpo-dir po/Text work/Text work2/Text
  sakuna.py pack    work2/Text         Text.mod.arc
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Tuple

try:
    import lz4.block as _lz4_block
except ImportError:  # pragma: no cover
    _lz4_block = None  # type: ignore


# --------------------------------------------------------------------------- #
# ARC / TGP0
# --------------------------------------------------------------------------- #

MAGIC = b"TGP0"
HEADER_SIZE = 0x10
ENTRY_SIZE = 0x70
NAME_SIZE = 0x60
COMPRESSION_LZ4 = 0x02
MANIFEST_NAME = "manifest.json"
CSV_EXTENSIONS = (".csvtxt", ".csvq", ".csvwl", ".csvcr", ".csvtr", ".csv")


class SakunaError(RuntimeError):
    pass


def _require_lz4():
    if _lz4_block is None:
        raise SakunaError("Das Modul 'lz4' fehlt:  python3 -m pip install lz4")
    return _lz4_block


def read_arc(path: str) -> Tuple[List[dict], bytes]:
    """Liest ein ARC. Gibt (Eintraege, dekomprimierter Datenstrom) zurueck."""
    with open(path, "rb") as fh:
        raw = fh.read()

    if raw[:4] != MAGIC:
        raise SakunaError(f"{path}: falsches Magic {raw[:4]!r} (erwartet TGP0)")

    version, comp, count, original_size = _unpack_from("<HHII", raw, 4)
    data_start = HEADER_SIZE + count * ENTRY_SIZE
    if data_start > len(raw):
        raise SakunaError(f"{path}: Tabellenende liegt ausserhalb der Datei")

    entries: List[dict] = []
    for i in range(count):
        off = HEADER_SIZE + i * ENTRY_SIZE
        name = raw[off : off + NAME_SIZE].split(b"\x00", 1)[0].decode("latin-1")
        offset, size, u1, u2 = _unpack_from("<IIII", raw, off + NAME_SIZE)
        entries.append({"name": name, "offset": offset, "size": size, "u1": u1, "u2": u2})

    payload = raw[data_start:]
    if comp == COMPRESSION_LZ4:
        block = _require_lz4()
        try:
            data = block.decompress(payload, uncompressed_size=original_size)
        except Exception as exc:  # noqa: BLE001
            raise SakunaError(f"{path}: LZ4-Dekompression fehlgeschlagen: {exc}") from exc
        if len(data) != original_size:
            raise SakunaError(
                f"{path}: Groesse {len(data)} != OriginalSize {original_size}"
            )
    elif comp == 0:
        data = payload
        if original_size and original_size != len(data):
            raise SakunaError(f"{path}: OriginalSize {original_size} != {len(data)}")
    else:
        raise SakunaError(f"{path}: unbekannter CompressionType {comp:#x}")

    return entries, data


def write_arc(
    path: str,
    entries: List[dict],
    data: bytes,
    compress: bool = True,
    fast: bool = False,
) -> None:
    """Schreibt ein ARC aus Eintraegen + dekomprimiertem Datenstrom."""
    table = bytearray()
    offset = 0
    for ent in entries:
        chunk = data[offset : offset + ent["size"]]
        if len(chunk) != ent["size"]:
            raise SakunaError(
                f"Eintrag {ent['name']}: erwartet {ent['size']} Bytes, "
                f"gefunden {len(chunk)} (Stimmen Eintraege und Daten ueberein?)"
            )
        name = ent["name"].encode("latin-1")
        if len(name) > NAME_SIZE:
            raise SakunaError(f"Name zu lang: {ent['name']!r}")
        table += name.ljust(NAME_SIZE, b"\x00")
        table += _pack("<IIII", offset, ent["size"], ent.get("u1", 0), ent.get("u2", 0))
        offset += ent["size"]

    if offset != len(data):
        raise SakunaError(
            f"Datenstrom {len(data)} Bytes, aber Eintraege decken nur {offset} ab"
        )

    comp = COMPRESSION_LZ4 if compress else 0
    header = _pack("<4sHHII", MAGIC, 3, comp, len(entries), len(data))
    if compress:
        block = _require_lz4()
        # "default"/"fast" ist ~40 % groesser als das Original, deshalb HC.
        payload = block.compress(
            data,
            store_size=False,
            mode="fast" if fast else "high_compression",
        )
    else:
        payload = data

    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(table)
        fh.write(payload)


def extract_arc(arc_path: str, out_dir: str, force: bool = False) -> int:
    entries, data = read_arc(arc_path)
    if os.path.exists(out_dir) and not force:
        raise SakunaError(f"{out_dir} existiert bereits (force mit --force)")
    os.makedirs(out_dir, exist_ok=True)

    manifest = {"source": os.path.basename(arc_path), "entries": []}
    for ent in entries:
        rel = ent["name"].replace("\\", "/")
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest) or out_dir, exist_ok=True)
        chunk = data[ent["offset"] : ent["offset"] + ent["size"]]
        with open(dest, "wb") as fh:
            fh.write(chunk)
        manifest["entries"].append({"name": ent["name"], "u1": ent["u1"], "u2": ent["u2"]})

    with open(os.path.join(out_dir, MANIFEST_NAME), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
    return len(entries)


def build_arc(in_dir: str, arc_path: str, compress: bool = True, fast: bool = False) -> int:
    manifest_path = os.path.join(in_dir, MANIFEST_NAME)
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        order = [(e["name"], e.get("u1", 0), e.get("u2", 0)) for e in manifest["entries"]]
    else:
        # Ohne Manifest: alphabetischer Durchlauf, Unbekannte auf 0
        found = []
        for root, _dirs, files in os.walk(in_dir):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, in_dir).replace(os.sep, "/")
                found.append(rel)
        order = [(p.replace("/", "\\"), 0, 0) for p in sorted(found)]

    entries, chunks = [], []
    for name, u1, u2 in order:
        file_path = os.path.join(in_dir, name.replace("\\", "/"))
        if not os.path.isfile(file_path):
            raise SakunaError(f"Datei fehlt: {file_path}")
        with open(file_path, "rb") as fh:
            blob = fh.read()
        entries.append({"name": name, "size": len(blob), "u1": u1, "u2": u2})
        chunks.append(blob)

    data = b"".join(chunks)
    write_arc(arc_path, entries, data, compress=compress, fast=fast)
    return len(entries)


# --------------------------------------------------------------------------- #
# Helfer (klein, damit keine weiteren Abhaengigkeiten noetig sind)
# --------------------------------------------------------------------------- #

import struct  # noqa: E402  (bewusst nach den ARC-Funktionen)


def _unpack_from(fmt: str, buf: bytes, off: int):
    return struct.unpack_from(fmt, buf, off)


def _pack(fmt: str, *values) -> bytes:
    return struct.pack(fmt, *values)


# --------------------------------------------------------------------------- #
# PO (gettext) - Quell- und Zielspalte sind unabhaengig waehlbar
# --------------------------------------------------------------------------- #

# Standardzuordnung Quellspalte (Englisch) -> Zielspalte (Spanisch).
FIELD_MAP: Dict[str, str] = {
    "English": "Spanish",
    "PostEn": "PostSp",
    "NameEn": "NameSp",
    "CommentEn": "CommentSp",
    "Floor_NameEn": "Floor_NameSp",
    "Enchant_NameEn": "Enchant_NameSp",
    "TextEn": "Spanish",
}

# Ziel-Spalten, die je Datei anders heissen koennen (Travel: 16x "Spanish",
# 2x "TextSp") - in csv_to_po nach der Primärziel aufgelöst.
DST_ALIASES: Dict[str, Tuple[str, ...]] = {
    "TextEn": ("TextSp",),
}


def _po_escape(value: str) -> str:
    out = []
    for ch in value:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


def _po_unescape(value: str) -> str:
    out, i = [], 0
    while i < len(value):
        ch = value[i]
        if ch != "\\" or i + 1 >= len(value):
            out.append(ch)
            i += 1
            continue
        nxt = value[i + 1]
        i += 2
        if nxt == "n":
            out.append("\n")
        elif nxt == "t":
            out.append("\t")
        elif nxt == "r":
            out.append("\r")
        elif nxt == "\\" or nxt == '"':
            out.append(nxt)
        else:
            out.append("\\" + nxt)
    return "".join(out)


def _scan_segment(seg: str) -> Tuple[str, bool]:
    """Liest einen Abschnitt, der mit '"' beginnt.

    Rueckgabe: (Inhalt ohne Anfuehrungszeichen, vollstaendig?).
    """
    if not seg.startswith('"'):
        return "", True
    out: List[str] = []
    i, n = 1, len(seg)
    while i < n:
        ch = seg[i]
        if ch == "\\" and i + 1 < n:
            out.append(_po_unescape("\\" + seg[i + 1]))
            i += 2
            continue
        if ch == '"':
            return "".join(out), True
        out.append(ch)
        i += 1
    return "".join(out), False


def _read_quoted(lines: List[str], start: int) -> Tuple[str, int]:
    """Liest den String einer msgctxt/msgid/msgstr-Zeile (ggf. fortgesetzt).

    Fortsetzungszeilen werden direkt angehaengt (gettext-Konvention);
    echte Zeilenumbrueche stehen als \\n-Escape im Text.
    Rueckgabe: (Wert, Index der naechsten zu behandelnden Zeile).
    """
    i = start
    if i >= len(lines):
        return "", i

    pos = lines[i].find('"')
    if pos < 0:
        # z.B.  msgid  allein, String steht in der Folgezeile
        i += 1
        if i >= len(lines) or not lines[i].lstrip().startswith('"'):
            return "", i
        pos = 0
    seg = lines[i][pos:]

    parts: List[str] = []
    while True:
        value, done = _scan_segment(seg)
        parts.append(value)
        i += 1
        if done:
            if i < len(lines) and lines[i].lstrip().startswith('"'):
                seg = lines[i].lstrip()
                continue
            break
        if i >= len(lines):
            break
        if not lines[i].lstrip().startswith('"'):
            # unvollstaendiges Anfuehrungszeichen -> Zeilenende ist Teil des Textes
            parts.append("\n" + lines[i])
            i += 1
            break
        seg = lines[i].lstrip()
    return "".join(parts), i


def parse_po(path: str) -> Tuple[Dict[str, str], List[dict]]:
    """Parst eine .po-Datei. Rueckgabe: (Header, Eintraege).

    Jeder Eintrag enthaelt zusaetzlich "code" (aus dem vorangehenden
    `#: row:N code:CODE field:F`-Kommentar; None, wenn keiner da ist).
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    header: Dict[str, str] = {}
    entries: List[dict] = []
    i = 0
    n = len(lines)
    pending_code: object = None
    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("#"):
            if line.startswith("#:") and " code:" in line and " field:" in line:
                pending_code = line.split(" code:", 1)[1].split(" field:", 1)[0]
            i += 1
            continue
        if line.startswith("msgctxt"):
            ctx, i = _read_quoted(lines, i)
            msgid, i = _read_quoted(lines, i)
            msgstr, i = _read_quoted(lines, i)
            entries.append(
                {"msgctxt": ctx, "msgid": msgid, "msgstr": msgstr, "code": pending_code}
            )
            pending_code = None
            continue
        if line.startswith("msgid"):
            pending_code = None
            msgid, i = _read_quoted(lines, i)
            msgstr, i = _read_quoted(lines, i)
            if msgid == "":
                # Header
                for part in msgstr.split("\n"):
                    if ":" in part:
                        key, _sep, val = part.partition(":")
                        header[key.strip()] = val.strip()
            continue
        i += 1
    return header, entries


def _append_columns(rows: List[str], missing: List[str]) -> List[str]:
    """Haengt Spalten an Kopf UND Zeilen an (sonst stimmt die Feldzahl nicht)."""
    if not missing:
        return rows
    old_count = len(rows[0].split(","))
    rows[0] = rows[0] + "".join("," + c for c in missing)
    for i in range(1, len(rows)):
        if not rows[i]:
            continue
        if len(rows[i].split(",")) == old_count:
            rows[i] = rows[i] + "," * len(missing)
    return rows


def csv_to_po(
    csv_path: str,
    po_path: str,
    field_map: Dict[str, str],
    add_column: bool = True,
    rel_name: str = "",
) -> Tuple[int, List[str]]:
    """Erzeugt aus einer CSV eine .po. Quellspalte bleibt unberuehrt.

    msgid = Quellspalte (z.B. Englisch), msgstr = leer -> wird Zielspalte.
    Rueckgabe: (Anzahl Eintraege, Hinweise).
    """
    with open(csv_path, "rb") as fh:
        raw = fh.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    rows = text.split("\r")
    fields = rows[0].split(",")

    notes: List[str] = []
    pairs = []
    for s, d in field_map.items():
        if s not in fields:
            continue
        if d not in fields:
            for alt in DST_ALIASES.get(s, ()):
                if alt in fields:
                    d = alt
                    break
        pairs.append((s, d))
    if not pairs:
        return 0, [f"keine Quellspalte gefunden in {csv_path}"]

    missing = [d for _s, d in pairs if d not in fields]
    if missing:
        if not add_column:
            return 0, [f"Zielspalte fehlt ({', '.join(missing)}) - uebersprungen"]
        rows = _append_columns(rows, missing)
        fields = rows[0].split(",")
        notes.append(f"Zielspalte angefuegt: {', '.join(missing)}")

    entries: List[str] = []
    count = 0
    for row_idx in range(1, len(rows)):
        row = rows[row_idx]
        if not row:
            continue
        cells = row.split(",")
        if len(cells) != len(fields):
            notes.append(f"Zeile {row_idx}: {len(cells)} statt {len(fields)} Feldern")
            continue
        code = cells[0]
        for src, dst in pairs:
            s_val = cells[fields.index(src)]
            d_val = cells[fields.index(dst)]
            msgid = s_val if s_val else d_val
            if not msgid:
                continue
            entries.append(f"#: row:{row_idx} code:{code} field:{src}")
            entries.append(f'msgctxt "{_po_escape(src + "#" + str(row_idx))}"')
            entries.append(f'msgid "{_po_escape(msgid.replace(chr(92) + "1", ","))}"')
            entries.append(f'msgstr ""')
            entries.append("")
            count += 1

    head = [
        "msgid \"\"",
        "msgstr \"\"",
        f'"Project-Id-Version: SakunaDeutsch 1.0\\n"',
        f'"Sakuna-File: {_po_escape(rel_name or os.path.basename(csv_path))}\\n"',
        f'"Sakuna-Src: {",".join(s for s, _d in pairs)}\\n"',
        f'"Sakuna-Dst: {",".join(d for _s, d in pairs)}\\n"',
        f'"Sakuna-Bom: {1 if bom else 0}\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Language: de\\n"',
        "",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(po_path)) or ".", exist_ok=True)
    with open(po_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(head + entries))
    return count, notes


def po_to_csv(po_path: str, csv_path: str, out_path: str) -> Tuple[int, List[str]]:
    """Schreibt uebersetzte msgstr-Zeilen in die Zielspalte der Original-CSV.

    Nicht uebersetzte Eintraege (msgstr leer) bleiben unangetastet.
    """
    header, entries = parse_po(po_path)
    if "Sakuna-Dst" not in header:
        raise SakunaError(f"{po_path}: Header 'Sakuna-Dst' fehlt")
    dst_fields = [x for x in header["Sakuna-Dst"].split(",") if x]
    src_fields = [x for x in header.get("Sakuna-Src", "").split(",") if x]
    # Src/Dst sind parallel aufgelistet - die im PO aufgeloeste Ziel-
    # spalte hat Vorrang (z.B. TextEn -> Spanish je Datei TextSp).
    hdr_dst = dict(zip(src_fields, dst_fields))
    reverse = {v: k for k, v in FIELD_MAP.items()}

    with open(csv_path, "rb") as fh:
        raw = fh.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if header.get("Sakuna-Bom") == "1" and not bom:
        bom = True
    text = raw.decode("utf-8-sig")
    rows = text.split("\r")
    fields = rows[0].split(",")

    # Spalten nur ergaenzen, wenn tatsaechlich etwas eingetragen wird -
    # sonst entstehen leere Zielspalten in bisher unuebersetzten Dateien.
    has_translation = any(e["msgstr"] for e in entries)
    missing = [name for name in dst_fields if name not in fields] if has_translation else []
    if missing:
        rows = _append_columns(rows, missing)
        fields = rows[0].split(",")
        notes_pre = f"Zielspalte angefuegt: {', '.join(missing)}"
    elif dst_fields and not any(name in fields for name in dst_fields) and not has_translation:
        notes_pre = f"keine Zielspalte, keine Uebersetzung - Datei bleibt unveraendert"
    else:
        notes_pre = ""
    notes: List[str] = []
    if notes_pre:
        notes.append(notes_pre)

    written = 0
    for ent in entries:
        msgstr = ent["msgstr"]
        if not msgstr:
            continue
        ctx = ent["msgctxt"]
        if "#" not in ctx:
            notes.append(f"msgctxt ohne Zeilenindex: {ctx!r}")
            continue
        src_field, row_s = ctx.rsplit("#", 1)
        if not row_s.isdigit():
            notes.append(f"msgctxt ohne Zeilenindex: {ctx!r}")
            continue
        row_idx = int(row_s)
        if row_idx >= len(rows):
            notes.append(f"Zeile {row_idx} existiert nicht mehr")
            continue
        dst_field = hdr_dst.get(src_field) or FIELD_MAP.get(src_field, reverse.get(src_field))
        if dst_field is None or dst_field not in fields:
            notes.append(f"keine Zielspalte fuer {src_field!r}")
            continue

        cells = rows[row_idx].split(",")
        if len(cells) != len(fields):
            notes.append(f"Zeile {row_idx}: Feldzahl passt nicht")
            continue
        value = msgstr.replace(",", "\\1")
        if "\r" in value:
            notes.append(f"Zeile {row_idx}: Zeilenumbruch entfernt")
            value = value.replace("\r", "\n")
        cells[fields.index(dst_field)] = value
        rows[row_idx] = ",".join(cells)
        written += 1

    out = "\r".join(rows)
    data = out.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(data)
    return written, notes


# --------------------------------------------------------------------------- #
# Stapelverarbeitung
# --------------------------------------------------------------------------- #


def _iter_csv(root: str):
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            if fn == MANIFEST_NAME:
                continue
            if fn.lower().endswith(CSV_EXTENSIONS):
                full = os.path.join(dirpath, fn)
                yield os.path.relpath(full, root), full


def po_dir(csv_root: str, po_root: str, field_map: Dict[str, str], add_column: bool) -> None:
    total = 0
    skipped = []
    for rel, full in _iter_csv(csv_root):
        po_path = os.path.join(po_root, rel)
        po_path = os.path.splitext(po_path)[0] + ".po"
        os.makedirs(os.path.dirname(po_path) or po_root, exist_ok=True)
        count, notes = csv_to_po(full, po_path, field_map, add_column, rel_name=rel)
        total += count
        if count == 0:
            skipped.append((rel, "; ".join(notes) or "keine Spalten"))
            if os.path.exists(po_path):
                os.remove(po_path)
        else:
            for note in notes:
                print(f"  Hinweis {rel}: {note}")
    print(f"{total} Uebersetzungs-Eintraege aus {len(list(_iter_csv(csv_root)))} Dateien.")
    if skipped:
        print("uebersprungen:")
        for rel, why in skipped:
            print(f"  {rel}: {why}")


def unpo_dir(po_root: str, csv_root: str, out_root: str) -> None:
    """Spielt alle .po auf CSV zurueck.

    Ist out_root noch nicht vorhanden, wird der komplette csv_root dorthin
    kopiert (sonst fehlen beim Packen alle nicht-uebersetzten Dateien).
    """
    if not os.path.exists(out_root):
        import shutil

        if not os.path.isdir(csv_root):
            raise SakunaError(f"{csv_root} existiert nicht")
        shutil.copytree(csv_root, out_root)
        print(f"Arbeitskopie angelegt: {out_root}")
    elif not os.path.isfile(os.path.join(out_root, MANIFEST_NAME)):
        print(
            f"ACHTUNG: {out_root} hat kein {MANIFEST_NAME} - es sieht aus wie ein "
            f"unvollstaendiger Ausgabeordner. Fuer 'pack' wird der komplette "
            f"entpackte Baum benoetigt."
        )

    done = 0
    for dirpath, _dirs, files in os.walk(po_root):
        for fn in sorted(files):
            if not fn.endswith(".po"):
                continue
            po_path = os.path.join(dirpath, fn)
            rel_dir = os.path.relpath(dirpath, po_root)
            rel_po = os.path.join(rel_dir, fn) if rel_dir != "." else fn
            header, _entries = parse_po(po_path)
            rel_csv = header.get("Sakuna-File") or (os.path.splitext(rel_po)[0])
            csv_path = os.path.join(csv_root, rel_csv)
            if not os.path.isfile(csv_path):
                print(f"  FEHLT: {csv_path}")
                continue
            out_path = os.path.join(out_root, rel_csv)
            written, notes = po_to_csv(po_path, csv_path, out_path)
            done += written
            for note in notes:
                print(f"  Hinweis {rel_csv}: {note}")
            print(f"  {rel_csv}: {written} Zeilen ueberschrieben")
    print(f"gesamt {done} Zeilen geschrieben.")


# --------------------------------------------------------------------------- #
# Pruefung uebersetzter Dateien
# --------------------------------------------------------------------------- #

MARKUP_CHARS = ("~", "^", "\\1")


def validate_csv(
    csv_path: str,
    src_field: str,
    dst_field: str,
    max_ratio: float = 1.6,
) -> Tuple[List[str], List[str]]:
    """Prueft eine uebersetzte CSV.

    Fehler (exit-Code 1):
      * ungueltiges UTF-8
      * Feldzahl weicht vom Kopf ab  -> CSV waere unbrauchbar
      * Zielspalte fehlt
      * ungerade Anzahl '~' oder '^' -> Markup nicht geschlossen
    Hinweise (nur Ausgabe):
      * Ziel deutlich laenger als Quelle (HUD-Boxen sind feste Pixelmasse)
      * andere Anzahl '\1' (Komma) als in der Quelle - bei echten
        Uebersetzungen normal, deshalb keine Warnung
    """
    errors: List[str] = []
    hints: List[str] = []
    with open(csv_path, "rb") as fh:
        raw = fh.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"{csv_path}: keine gueltige UTF-8: {exc}"], []

    rows = text.split("\r")
    fields = rows[0].split(",")
    if src_field not in fields:
        return [f"{csv_path}: Quellspalte {src_field!r} fehlt"], []
    if dst_field not in fields:
        return [f"{csv_path}: Zielspalte {dst_field!r} fehlt"], []

    si, di = fields.index(src_field), fields.index(dst_field)
    for idx in range(1, len(rows)):
        row = rows[idx]
        if not row:
            continue
        cells = row.split(",")
        if len(cells) != len(fields):
            errors.append(f"Zeile {idx}: {len(cells)} statt {len(fields)} Feldern")
            continue
        src, dst = cells[si], cells[di]
        if not dst:
            continue
        for ch in ("~", "^"):
            if dst.count(ch) % 2:
                errors.append(
                    f"Zeile {idx}: Markup {ch!r} {dst.count(ch)}x - nicht geschlossen"
                )
        if src:
            if dst.count("\\1") != src.count("\\1"):
                hints.append(
                    f"Zeile {idx}: \\1 {src.count('\\1')}x Quelle vs "
                    f"{dst.count('\\1')}x Ziel"
                )
            if len(dst) > len(src) * max_ratio and len(dst) - len(src) > 8:
                hints.append(
                    f"Zeile {idx}: Ziel {len(dst)} Zeichen vs Quelle {len(src)} "
                    f"(Faktor {len(dst) / len(src):.2f})"
                )
    return errors, hints


def validate_tree(root: str, src_field: str, dst_field: str, max_ratio: float) -> int:
    bad_files = total_err = total_hint = 0
    for rel, full in _iter_csv(root):
        errors, hints = validate_csv(full, src_field, dst_field, max_ratio)
        total_err += len(errors)
        total_hint += len(hints)
        if errors:
            bad_files += 1
            print(f"{rel}:")
            for issue in errors[:20]:
                print(f"   FEHLER {issue}")
            if len(errors) > 20:
                print(f"   ... {len(errors) - 20} weitere Fehler")
    print(f"{total_err} Fehler in {bad_files} Datei(en), {total_hint} Hinweis(e).")
    return 1 if bad_files else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _field_map_from_args(args) -> Dict[str, str]:
    if getattr(args, "src", None) and getattr(args, "dst", None):
        return {args.src: args.dst}
    return dict(FIELD_MAP)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sakuna.py",
        description="Sakuna-Archive und Uebersetzungs-CSVs bearbeiten.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("extract", help="ARC entpacken")
    p.add_argument("arc")
    p.add_argument("outdir")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("pack", help="Verzeichnis zu einem ARC packen")
    p.add_argument("indir")
    p.add_argument("arc")
    p.add_argument("--raw", action="store_true", help="ohne LZ4 packen")
    p.add_argument("--fast", action="store_true", help="schnell, aber groessere Datei")

    p = sub.add_parser("to-po", help="CSV -> .po")
    p.add_argument("csv")
    p.add_argument("po")
    p.add_argument("--src", help="Quellspalte, z.B. English (Standard: alle Paare)")
    p.add_argument("--dst", help="Zielspalte, z.B. Spanish")
    p.add_argument(
        "--root",
        help="Wurzel des entpackten Baums - daraus wird der relative Pfad "
        "im PO-Header ermittelt (wichtig fuer unpo-dir)",
    )
    p.add_argument(
        "--add-column",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="fehlende Zielspalte anhaengen",
    )

    p = sub.add_parser("from-po", help=".po + Original-CSV -> neue CSV")
    p.add_argument("po")
    p.add_argument("csv")
    p.add_argument("out")

    p = sub.add_parser("po-dir", help="alle CSV unter Ordner nach .po")
    p.add_argument("csvroot")
    p.add_argument("poroot")
    p.add_argument("--src")
    p.add_argument("--dst")
    p.add_argument(
        "--add-column",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    p = sub.add_parser("unpo-dir", help="alle .po zurueck auf CSV")
    p.add_argument("poroot")
    p.add_argument("csvroot")
    p.add_argument("outroot")

    p = sub.add_parser("validate", help="eine uebersetzte CSV pruefen")
    p.add_argument("csv")
    p.add_argument("--src", default="English")
    p.add_argument("--dst", default="Spanish")
    p.add_argument("--max-ratio", type=float, default=1.6)

    p = sub.add_parser("validate-dir", help="ganzen Baum pruefen")
    p.add_argument("root")
    p.add_argument("--src", default="English")
    p.add_argument("--dst", default="Spanish")
    p.add_argument("--max-ratio", type=float, default=1.6)

    args = parser.parse_args(argv)

    try:
        if args.cmd == "extract":
            n = extract_arc(args.arc, args.outdir, force=args.force)
            print(f"{n} Dateien entpackt nach {args.outdir}")
        elif args.cmd == "pack":
            n = build_arc(args.indir, args.arc, compress=not args.raw, fast=args.fast)
            print(f"{n} Dateien gepackt -> {args.arc}")
        elif args.cmd == "to-po":
            rel = None
            if getattr(args, "root", None):
                rel = os.path.relpath(args.csv, args.root).replace(os.sep, "/")
            count, notes = csv_to_po(
                args.csv, args.po, _field_map_from_args(args), args.add_column,
                rel_name=rel or "",
            )
            for note in notes:
                print(f"Hinweis: {note}")
            print(f"{count} Eintraege -> {args.po}")
        elif args.cmd == "from-po":
            count, notes = po_to_csv(args.po, args.csv, args.out)
            for note in notes:
                print(f"Hinweis: {note}")
            print(f"{count} Zeilen geschrieben -> {args.out}")
        elif args.cmd == "po-dir":
            po_dir(args.csvroot, args.poroot, _field_map_from_args(args), args.add_column)
        elif args.cmd == "unpo-dir":
            unpo_dir(args.poroot, args.csvroot, args.outroot)
        elif args.cmd == "validate":
            errors, hints = validate_csv(args.csv, args.src, args.dst, args.max_ratio)
            for issue in errors:
                print(f"FEHLER {issue}")
            for issue in hints:
                print(f"Hinweis {issue}")
            print(f"{len(errors)} Fehler, {len(hints)} Hinweis(e).")
            return 1 if errors else 0
        elif args.cmd == "validate-dir":
            return validate_tree(args.root, args.src, args.dst, args.max_ratio)
    except SakunaError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
