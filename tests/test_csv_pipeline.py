"""CSV-Pipeline: _iter_csv-Erweiterungen, CR-Zeilensplit, csv_to_po/po_to_csv.

Zwei dokumentierte Rezidive:
  * CSV_EXTENSIONS musste JEDES uebersetzbare Suffix listen — das fehlende
    '.csvtr' liess die komplette Travel-Gruppe stillschweigend weg.
  * Zeilen duerfen NUR auf '\\r' getrennt werden; Zellen halten echtes '\\n'.
    `re.split(r'\\r\\n|\\r|\\n')` erzeugt Phantomzeilen.
"""

import pytest

import sakuna as S
from sakuna import CSV_EXTENSIONS, _iter_csv, csv_to_po, po_to_csv
from tests.conftest import read_csv_rows, write_csv


# --------------------------------------------------------------------------- #
# CSV_EXTENSIONS / _iter_csv
# --------------------------------------------------------------------------- #

ALLE_SUFFIXE = (".csvtxt", ".csvq", ".csvwl", ".csvcr", ".csvtr", ".csv")


def test_alle_uebersetzbaren_suffixe_gelistet():
    """Der '.csvtr'-Bug: jedes bekannte Suffix muss in CSV_EXTENSIONS stehen."""
    for suf in ALLE_SUFFIXE:
        assert suf in CSV_EXTENSIONS, f"{suf} fehlt in CSV_EXTENSIONS"


def test_iter_csv_findet_jedes_suffix(csv_root):
    expected = set()
    for suf in ALLE_SUFFIXE:
        rel = f"grp/File{suf}"
        write_csv(csv_root / rel, ["Code", "English"], [["A", "x"]])
        expected.add(rel.replace("\\", "/"))
        # Gross-/Kleinschreibung darf nicht aussteigen
        rel_up = f"grp/Up{suf.upper()}"
        write_csv(csv_root / rel_up, ["Code", "English"], [["A", "x"]])
        expected.add(rel_up.replace("\\", "/"))

    found = {rel.replace("\\", "/") for rel, _full in _iter_csv(str(csv_root))}
    assert found == expected


def test_iter_csv_ueberspringt_manifest(csv_root):
    write_csv(csv_root / "manifest.json", ["Code"], [["A"]])
    (csv_root / "manifest.json").write_text("{}", encoding="utf-8")
    write_csv(csv_root / "ok.csvtxt", ["Code", "English"], [["A", "x"]])
    found = [rel for rel, _ in _iter_csv(str(csv_root))]
    assert found == ["ok.csvtxt"]


def test_iter_csv_geht_rekursiv(csv_root):
    write_csv(csv_root / "tiefe" / "ebene" / "a.csvtr", ["Code", "English"], [["A", "x"]])
    found = [rel.replace("\\", "/") for rel, _ in _iter_csv(str(csv_root))]
    assert found == ["tiefe/ebene/a.csvtr"]


# --------------------------------------------------------------------------- #
# Zeilensplit NUR auf '\r'
# --------------------------------------------------------------------------- #


def test_zeilen_split_nur_auf_cr(tmp_path):
    """Zellen mit echtem '\n' duerfen keine Phantomzeilen erzeugen."""
    p = write_csv(
        tmp_path / "nl.csvtxt",
        ["Code", "English", "Spanish"],
        [["C1", "Zeile1\nZeile2\nZeile3", ""]],
        )
    rows = open(p, "rb").read().decode("utf-8-sig").split("\r")
    assert len(rows) == 2, "eine Kopfzeile + genau eine Datenzeile"

    fields, body = read_csv_rows(p)
    assert len(body) == 1
    assert body[0][1] == "Zeile1\nZeile2\nZeile3"


def test_csv_to_po_zaehlt_zeilen_mit_newlines_korrekt(tmp_path):
    p = write_csv(
        tmp_path / "nl.csvtxt",
        ["Code", "English", "Spanish"],
        [["C1", "A\nB", ""], ["C2", "plain", ""]],
    )
    po = str(tmp_path / "nl.po")
    count, notes = csv_to_po(p, po, {"English": "Spanish"}, rel_name="nl.csvtxt")
    assert count == 2
    assert notes == []


def test_newlines_ueberleben_roundtrip(tmp_path):
    from tests.conftest import fill_translations
    src = write_csv(
        tmp_path / "nl.csvtxt",
        ["Code", "English", "Spanish"],
        [["C1", "A\nB\nC", ""]],
    )
    po = str(tmp_path / "nl.po")
    csv_to_po(src, po, {"English": "Spanish"}, rel_name="nl.csvtxt")
    fill_translations(po, {"C1": "X\nY"})

    out = str(tmp_path / "out.csvtxt")
    written, notes = po_to_csv(po, src, out)
    assert written == 1
    fields, body = read_csv_rows(out)
    assert body[0][fields.index("English")] == "A\nB\nC", "Quelle unangetastet"
    assert body[0][fields.index("Spanish")] == "X\nY"


# --------------------------------------------------------------------------- #
# csv_to_po
# --------------------------------------------------------------------------- #


def test_csv_to_po_basiseintraege(tmp_path):
    p = write_csv(
        tmp_path / "b.csvtxt",
        ["Code", "English", "Spanish"],
        [["CODE_1", "Hello", ""], ["CODE_2", "World", "Welt"]],
    )
    po = str(tmp_path / "b.po")
    count, notes = csv_to_po(p, po, {"English": "Spanish"}, rel_name="b.csvtxt")
    assert count == 2

    header, entries = S.parse_po(po)
    assert header["Sakuna-File"] == "b.csvtxt"
    assert header["Sakuna-Src"] == "English"
    assert header["Sakuna-Dst"] == "Spanish"
    assert [e["code"] for e in entries] == ["CODE_1", "CODE_2"]
    # msgid = Quellspalte, msgstr leer (wird spaeter gefuellt)
    assert [e["msgid"] for e in entries] == ["Hello", "World"]
    assert [e["msgstr"] for e in entries] == ["", ""]
    assert [e["msgctxt"] for e in entries] == ["English#1", "English#2"]


def test_csv_to_po_ohne_quellspalte(tmp_path):
    p = write_csv(tmp_path / "o.csvtxt", ["Code", "Spanish"], [["C1", "x"]])
    count, notes = csv_to_po(p, str(tmp_path / "o.po"), {"English": "Spanish"})
    assert count == 0
    assert "keine Quellspalte" in notes[0]


def test_csv_to_po_fuellt_msgid_aus_zielspalte(tmp_path):
    """Ohne Quelle, aber mit Ziel: Ziel dient als msgid (schon uebersetzt)."""
    p = write_csv(tmp_path / "z.csvtxt", ["Code", "English", "Spanish"],
                  [["C1", "", "Vorhanden"]])
    po = str(tmp_path / "z.po")
    count, _ = csv_to_po(p, po, {"English": "Spanish"})
    assert count == 1
    _h, entries = S.parse_po(po)
    assert entries[0]["msgid"] == "Vorhanden"


def test_csv_to_po_komma_escaping(tmp_path):
    """Kommas in Zellen stehen als '\\1' und landen als ',' in der msgid."""
    p = write_csv(tmp_path / "k.csvtxt", ["Code", "English", "Spanish"],
                  [["C1", "A\\1 B", ""]])
    po = str(tmp_path / "k.po")
    csv_to_po(p, po, {"English": "Spanish"})
    _h, entries = S.parse_po(po)
    assert entries[0]["msgid"] == "A, B"


def test_csv_to_po_feldzahl_mismatch(tmp_path):
    p = tmp_path / "m.csvtxt"
    p.write_bytes(b"Code,English,Spanish\rC1,nur-zwei\rC2,a,b\r")
    po = str(tmp_path / "m.po")
    count, notes = csv_to_po(str(p), po, {"English": "Spanish"})
    assert count == 1
    assert any("Feldern" in n for n in notes)


def test_csv_to_po_bom_header(tmp_path):
    p = write_csv(tmp_path / "bom.csvtxt", ["Code", "English"], [["C1", "x"]], bom=True)
    po = str(tmp_path / "bom.po")
    csv_to_po(p, po, {"English": "Spanish"})
    header, _ = S.parse_po(po)
    assert header["Sakuna-Bom"] == "1"


# --------------------------------------------------------------------------- #
# po_to_csv
# --------------------------------------------------------------------------- #


def _po_with_translation(tmp_path, entries, dst="Spanish", src="English",
                         rel="t.csvtxt"):
    from tests.conftest import make_entry, write_po as _wp
    return _wp(tmp_path / "t.po", {
        "Sakuna-File": rel,
        "Sakuna-Src": src,
        "Sakuna-Dst": dst,
        "Sakuna-Bom": "0",
    }, entries)


def test_po_to_csv_schreibt_nur_msgstr(tmp_path):
    from tests.conftest import make_entry
    src = write_csv(tmp_path / "t.csvtxt", ["Code", "English", "Spanish"],
                    [["C1", "Hello", ""], ["C2", "World", "Welt"]])
    po = _po_with_translation(tmp_path, [
        make_entry("English#1", "Hello", "Hallo", "C1"),
        make_entry("English#2", "World", "", "C2"),   # nicht uebersetzt
    ])
    out = str(tmp_path / "out.csvtxt")
    written, notes = po_to_csv(str(po), src, out)
    assert written == 1

    fields, body = read_csv_rows(out)
    assert body[0][fields.index("Spanish")] == "Hallo"
    assert body[0][fields.index("English")] == "Hello", "Quelle bleibt"
    assert body[1][fields.index("Spanish")] == "Welt", "leere msgstr = unangetastet"


def test_po_to_csv_komma_wird_zu_1(tmp_path):
    from tests.conftest import make_entry
    src = write_csv(tmp_path / "t.csvtxt", ["Code", "English", "Spanish"],
                    [["C1", "x", ""]])
    po = _po_with_translation(tmp_path, [
        make_entry("English#1", "x", "A, B", "C1"),
    ])
    out = str(tmp_path / "out.csvtxt")
    po_to_csv(str(po), src, out)
    fields, body = read_csv_rows(out)
    assert body[0][fields.index("Spanish")] == "A\\1 B"


def test_po_to_csv_entfernt_cr_mit_hinweis(tmp_path):
    from tests.conftest import make_entry
    src = write_csv(tmp_path / "t.csvtxt", ["Code", "English", "Spanish"],
                    [["C1", "x", ""]])
    po = _po_with_translation(tmp_path, [
        make_entry("English#1", "x", "A\rB", "C1"),
    ])
    out = str(tmp_path / "out.csvtxt")
    written, notes = po_to_csv(str(po), src, out)
    assert written == 1
    assert any("Zeilenumbruch" in n for n in notes)
    fields, body = read_csv_rows(out)
    assert body[0][fields.index("Spanish")] == "A\nB"


def test_po_to_csv_ohne_dst_header_schlaegt_fehl(tmp_path):
    from tests.conftest import make_entry, write_po as _wp
    src = write_csv(tmp_path / "t.csvtxt", ["Code", "English"], [["C1", "x"]])
    po = _wp(tmp_path / "t.po", {"Sakuna-File": "t.csvtxt"},
             [make_entry("English#1", "x", "y", "C1")])
    with pytest.raises(S.SakunaError):
        po_to_csv(str(po), src, str(tmp_path / "out.csvtxt"))


def test_po_to_csv_unbekannte_zeile(tmp_path):
    from tests.conftest import make_entry
    src = write_csv(tmp_path / "t.csvtxt", ["Code", "English", "Spanish"],
                    [["C1", "x", ""]])
    po = _po_with_translation(tmp_path, [
        make_entry("English#99", "x", "y", "C1"),
    ])
    out = str(tmp_path / "out.csvtxt")
    written, notes = po_to_csv(str(po), src, out)
    assert written == 0
    assert any("existiert nicht mehr" in n for n in notes)


# --------------------------------------------------------------------------- #
# End-to-End: csv_to_po -> msgstr fuellen -> po_to_csv
# --------------------------------------------------------------------------- #


def test_roundtrip_ueber_zwei_dateien(tmp_path):
    from tests.conftest import fill_translations
    # Komma in Zelle steht als '\1' (Spielkonvention), nicht als ','
    rows = [
        ["C_START", "Start Game", ""],
        ["C_LOAD", "Load\\1 Game", ""],
        ["C_MULTI", "Line one\nLine two", ""],
    ]
    src = write_csv(tmp_path / "ui.csvtxt", ["Code", "English", "Spanish"], rows)
    po = str(tmp_path / "ui.po")
    count, _ = csv_to_po(src, po, {"English": "Spanish"}, rel_name="ui.csvtxt")
    assert count == 3

    fill_translations(po, {
        "C_START": "Spiel starten",
        "C_LOAD": "Spiel laden",
        "C_MULTI": "Zeile eins\nZeile zwei",
    })

    out = str(tmp_path / "ui_out.csvtxt")
    written, notes = po_to_csv(po, src, out)
    assert written == 3
    assert notes == []

    fields, body = read_csv_rows(out)
    assert [r[0] for r in body] == ["C_START", "C_LOAD", "C_MULTI"]
    assert body[0][fields.index("English")] == "Start Game"
    assert body[0][fields.index("Spanish")] == "Spiel starten"
    assert body[1][fields.index("English")] == "Load\\1 Game", "Quelle bleibt"
    assert body[1][fields.index("Spanish")] == "Spiel laden"
    assert body[2][fields.index("Spanish")] == "Zeile eins\nZeile zwei"
    assert body[2][fields.index("English")] == "Line one\nLine two"
