"""parse_po / write_po: Escaping, Fortsetzungszeilen, Code-Kommentare.

Regressionsgrund: write_po musste die `#: code:`-Kommentare mitschreiben,
sonst bricht der Code-Lookup nach dem naechsten Apply-Lauf (Absicht lt.
Commit fc3fbf9). Dazu der Escape-Roundtrip fuer \\ \" \\n \\r \\t.
"""

import pytest

import apply_de
import sakuna as S
from tests.conftest import make_entry, write_po


# --------------------------------------------------------------------------- #
# Escape-Roundtrip
# --------------------------------------------------------------------------- #

NASTY = [
    "",
    "einfach",
    "mit , Komma",
    "mit \\1 Platzhalter",
    "Backslash \\ am Ende",
    "Quote \" und ' dabei",
    "Zeilen\nbruch",
    "Tab\tstop",
    "Wagenrueck\rkehr",
    "alles: \\\" \n \r \t \\\\ kombiniert",
    "Umlaute ÄÖÜ äöü ß",
    "Emoji 🌾 Sakuna",
]


@pytest.mark.parametrize("value", NASTY)
def test_po_escape_roundtrip(value):
    assert S._po_unescape(S._po_escape(value)) == value


@pytest.mark.parametrize("value", NASTY)
def test_po_escape_faengt_sonderzeichen(value):
    esc = S._po_escape(value)
    # Zeilenumbrueche duerfen nie roh im String stehen
    assert "\n" not in esc
    assert "\r" not in esc
    # Jedes Anfuehrungszeichen muss maskiert sein
    assert esc.count('"') == esc.count('\\"')


def test_unescape_unbekannter_code_bleibt_roh():
    assert S._po_unescape("\\q") == "\\q"


# --------------------------------------------------------------------------- #
# parse_po
# --------------------------------------------------------------------------- #


def test_parse_po_header_und_eintraege(tmp_path):
    p = tmp_path / "x.po"
    p.write_text(
        'msgid ""\n'
        'msgstr ""\n'
        '"Sakuna-File: Event/Test.csvtxt\\n"\n'
        '"Sakuna-Dst: Spanish\\n"\n'
        "\n"
        '#: row:3 code:CODE_A field:English\n'
        'msgctxt "English#3"\n'
        'msgid "Hello"\n'
        'msgstr "Hallo"\n'
        "\n",
        encoding="utf-8",
    )
    header, entries = S.parse_po(str(p))
    assert header["Sakuna-File"] == "Event/Test.csvtxt"
    assert header["Sakuna-Dst"] == "Spanish"
    assert len(entries) == 1
    e = entries[0]
    assert e["msgctxt"] == "English#3"
    assert e["msgid"] == "Hello"
    assert e["msgstr"] == "Hallo"
    assert e["code"] == "CODE_A"


def test_parse_po_ohne_code_kommentar(tmp_path):
    p = tmp_path / "x.po"
    p.write_text(
        'msgctxt "English#1"\nmsgid "A"\nmsgstr "B"\n', encoding="utf-8"
    )
    _h, entries = S.parse_po(str(p))
    assert entries[0]["code"] is None


def test_parse_po_fortsetzungszeilen(tmp_path):
    p = tmp_path / "x.po"
    p.write_text(
        'msgctxt "English#1"\n'
        'msgid ""\n'
        '"erste "\n'
        '"zweite"\n'
        'msgstr ""\n'
        '"uebersetzt"\n',
        encoding="utf-8",
    )
    _h, entries = S.parse_po(str(p))
    assert entries[0]["msgid"] == "erste zweite"
    assert entries[0]["msgstr"] == "uebersetzt"


def test_parse_po_header_ist_leere_msgid(tmp_path):
    p = tmp_path / "x.po"
    p.write_text(
        'msgid ""\nmsgstr ""\n"Language: de\\n"\n', encoding="utf-8"
    )
    header, entries = S.parse_po(str(p))
    assert header["Language"] == "de"
    assert entries == []


# --------------------------------------------------------------------------- #
# write_po + Roundtrip
# --------------------------------------------------------------------------- #


def test_write_po_roundtrip_behaelt_code(tmp_path):
    entries = [make_entry("English#3", "Hello", "Hallo", code="CODE_A")]
    p = write_po(tmp_path / "out" / "t.po", dict(SAMPLE := {
        "Sakuna-File": "Event/Test.csvtxt",
        "Sakuna-Dst": "Spanish",
    }), entries)

    text = p.read_text(encoding="utf-8")
    assert "#: row:3 code:CODE_A field:English" in text

    header, parsed = S.parse_po(p)
    assert header["Sakuna-File"] == "Event/Test.csvtxt"
    assert parsed[0]["code"] == "CODE_A"
    assert parsed[0]["msgstr"] == "Hallo"


def test_write_po_roundtrip_escapes(tmp_path):
    for value in NASTY:
        entries = [make_entry("English#1", "src", value, code="C1")]
        p = write_po(tmp_path / "e.po", {"Sakuna-File": "T.csvtxt"}, entries)
        _h, parsed = S.parse_po(str(p))
        assert parsed[0]["msgstr"] == value, value


def test_write_po_ohne_code_kein_kommentar(tmp_path):
    entries = [make_entry("English#5", "x", "y", code=None)]
    p = write_po(tmp_path / "n.po", {"Sakuna-File": "T.csvtxt"}, entries)
    assert "#:" not in p.read_text(encoding="utf-8")


def test_write_po_schreibt_lf_als_newline(tmp_path):
    """PO-Dateien sind LF-getrennt (newline='\n'), nicht CRLF."""
    entries = [make_entry("English#1", "a", "b", code="C")]
    p = write_po(tmp_path / "lf.po", {"Sakuna-File": "T.csvtxt"}, entries)
    raw = p.read_bytes()
    assert b"\r" not in raw
