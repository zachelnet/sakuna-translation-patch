"""Gemeinsame Fixtures: CSV-/PO-Baukasten fuer die Pipeline-Tests.

Wichtiges Format-Detail (siehe MEMORY: "row diff must split rows ONLY on
'\\r'"): CSV-Zeilen sind durch CR getrennt, Zellen duerfen echte LF
enthalten. Alle Builder hier erzeugen deshalb CR-getrennte Bytes.
"""

import os
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import sakuna as S  # noqa: E402


# --------------------------------------------------------------------------- #
# CSV-Baukasten
# --------------------------------------------------------------------------- #


def build_csv_bytes(fields, rows, bom=False):
    """Baut CR-getrennte CSV-Bytes.

    rows: Liste von Listen aus Zell-Strings (Reihenfolge = fields).
    Zellen duerfen '\\n' enthalten; Kommas in Zellen muessen als '\\1'
    vorliegen (Spielkonvention), sonst zerlegt split(',') sie.
    """
    lines = [",".join(fields)]
    for row in rows:
        assert len(row) == len(fields), f"Zahl {len(row)} != {len(fields)} Felder"
        lines.append(",".join(row))
    data = "\r".join(lines).encode("utf-8")
    return (b"\xef\xbb\xbf" + data) if bom else data


def write_csv(path, fields, rows, bom=False):
    path = str(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(build_csv_bytes(fields, rows, bom=bom))
    return path


def read_csv_rows(path):
    """Liest eine CSV exakt wie die Pipeline: Split NUR auf '\\r'."""
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8-sig")
    rows = text.split("\r")
    fields = rows[0].split(",")
    body = []
    for row in rows[1:]:
        if not row:
            continue
        body.append(row.split(","))
    return fields, body


# --------------------------------------------------------------------------- #
# PO-Baukasten
# --------------------------------------------------------------------------- #

SAMPLE_HEADER = {
    "Project-Id-Version": "sakuna-translation-patch test",
    "Sakuna-File": "Event/Test.csvtxt",
    "Sakuna-Src": "English",
    "Sakuna-Dst": "Spanish",
    "Sakuna-Bom": "0",
}


def make_entry(ctx, msgid, msgstr="", code=None):
    return {"msgctxt": ctx, "msgid": msgid, "msgstr": msgstr, "code": code}


def write_po(path, header, entries):
    """Nutzt apply_de.write_po, damit Code-Kommentare wie im Produkt landen."""
    import apply_de

    path = str(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    apply_de.write_po(path, header, entries)
    return Path(path)


def fill_translations(po_path, by_code):
    """Traegt msgstr nach Code ein (wie apply_de) und schreibt zurueck.

    by_code: {code: msgstr}; Codes ohne Eintrag bleiben leer.
    """
    import apply_de

    header, entries = S.parse_po(str(po_path))
    for e in entries:
        if e.get("code") in by_code:
            e["msgstr"] = by_code[e["code"]]
    apply_de.write_po(str(po_path), header, entries)
    return header, entries


@pytest.fixture
def csv_root(tmp_path):
    """Leeres Verzeichnis fuer CSV-Baeume."""
    d = tmp_path / "csv"
    d.mkdir()
    return d


@pytest.fixture
def po_root(tmp_path):
    d = tmp_path / "po"
    d.mkdir()
    return d


@pytest.fixture
def clean_de():
    """Stellt apply_de.DE nach dem Test wieder leer."""
    import apply_de

    old = dict(apply_de.DE)
    apply_de.DE = {}
    yield apply_de.DE
    apply_de.DE = old
