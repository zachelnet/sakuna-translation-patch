"""validate_csv: Fehler (exit 1) vs. Hinweise (nur Ausgabe).

Der Installer haengt am validate-dir-Gate auf mod/Text — was hier als
Fehler durchgeht, verhindert also die Installation.
"""

import pytest

import sakuna as S
from sakuna import validate_csv
from tests.conftest import write_csv


def _run(tmp_path, rows, fields=("Code", "English", "Spanish"), src="English",
         dst="Spanish", **kw):
    p = write_csv(tmp_path / "v.csvtxt", list(fields), rows)
    return validate_csv(str(p), src, dst, **kw)


def test_ok_datei_ist_fehlerfrei(tmp_path):
    errors, hints = _run(tmp_path, [["C1", "Hello", "Hallo"]])
    assert errors == []
    assert hints == []


def test_fehler_feldzahl_weicht_ab(tmp_path):
    p = tmp_path / "v.csvtxt"
    p.write_bytes(b"Code,English,Spanish\rC1,nur-zwei\r")
    errors, _ = validate_csv(str(p), "English", "Spanish")
    assert any("Feldern" in e for e in errors)


def test_fehler_quellspalte_fehlt(tmp_path):
    errors, _ = _run(tmp_path, [["C1", "y"]], fields=("Code", "Spanish"),
                     src="English", dst="Spanish")
    assert any("Quellspalte" in e for e in errors)


def test_fehler_zielspalte_fehlt(tmp_path):
    errors, _ = _run(tmp_path, [["C1", "x"]], fields=("Code", "English"),
                     src="English", dst="Spanish")
    assert any("Zielspalte" in e for e in errors)


@pytest.mark.parametrize("markup", ["~", "^"])
def test_fehler_markup_nicht_geschlossen(tmp_path, markup):
    errors, _ = _run(tmp_path, [["C1", "a", markup + "offen"]])
    assert any("nicht geschlossen" in e for e in errors)


@pytest.mark.parametrize("markup", ["~", "^"])
def test_ok_markup_geschlossen(tmp_path, markup):
    errors, _ = _run(tmp_path, [["C1", "a", markup + "zu" + markup]])
    assert errors == []


def test_hinweis_ziel_zu_lang(tmp_path):
    """Nur Hinweis, kein Fehler - HUD-Boxen sind feste Pixelmasse."""
    errors, hints = _run(tmp_path, [["C1", "kurz", "x" * 100]])
    assert errors == []
    assert any("Zeichen" in h for h in hints)


def test_kein_hinweis_bei_kurzer_dehnung(tmp_path):
    errors, hints = _run(tmp_path, [["C1", "abcd", "abcdefgh"]])
    assert errors == []
    assert hints == []


def test_hinweis_unterschiedliche_komma_anzahl(tmp_path):
    errors, hints = _run(tmp_path, [["C1", "a\\1 b", "nur eins"]])
    assert errors == []
    assert any("\\1" in h for h in hints)


def test_leere_zielspalte_wird_uebersprungen(tmp_path):
    errors, hints = _run(tmp_path, [["C1", "~kaputt", ""]])
    assert errors == []
    assert hints == []


def test_ungueltiges_utf8(tmp_path):
    p = tmp_path / "v.csvtxt"
    p.write_bytes(b"Code,English,Spanish\rC1,\xff\xfe,ok\r")
    errors, _ = validate_csv(str(p), "English", "Spanish")
    assert any("UTF-8" in e for e in errors)


def test_zeilen_mit_newline_gueltig(tmp_path):
    """Mehrzeilige Zellen sind normal - kein Fehler, keine Phantomzeile."""
    errors, _ = _run(tmp_path, [["C1", "a\nb", "x\ny"]])
    assert errors == []


def test_validate_tree_exit_code(tmp_path, capsys):
    root = tmp_path / "tree"
    write_csv(root / "ok.csvtxt", ["Code", "English", "Spanish"],
              [["C1", "a", "b"]])
    write_csv(root / "bad.csvtxt", ["Code", "English", "Spanish"],
              [["C1", "a", "~offen"]])
    rc = S.validate_tree(str(root), "English", "Spanish", 1.6)
    assert rc == 1
    out = capsys.readouterr().out
    assert "1 Fehler" in out


def test_validate_tree_ok(tmp_path, capsys):
    root = tmp_path / "tree"
    write_csv(root / "ok.csvtxt", ["Code", "English", "Spanish"],
              [["C1", "a", "b"]])
    rc = S.validate_tree(str(root), "English", "Spanish", 1.6)
    assert rc == 0
    assert "0 Fehler" in capsys.readouterr().out
