"""resolve(): Code-Key vor Zeilen-Key, Root-Prioritaet, Beta nur wenn aktiv.

Regressionsgrund: der Schema-Wechsel (fc3fbf9) hat Zeilen-Indizes durch
stabile Codes ersetzt. Genau diese Aufloesung traegt die Update-Festigkeit.
"""

import pytest

import apply_de
from apply_de import _MISSING, resolve


REL = "Text/Event/Soto/Test.csvtxt"
BASE = "Test"


@pytest.fixture
def de(clean_de):
    clean_de.update(
        {
            (REL, "English#c:CODE_A"): "Code-A-Treffer",
            (REL, "English#r:2"): "Zeilen-Treffer",
            (REL, "English#c:CODE_NONE"): None,          # absichtlich leer
            (REL + "#beta", "English#c:CODE_A"): "Beta-Treffer",
            (BASE, "English#c:CODE_BASE"): "Basenamen-Treffer",
        }
    )
    return clean_de


def test_code_key_schlaegt_zeilen_key(de):
    val = resolve(REL, BASE, "English#2", "CODE_A", False)
    assert val == "Code-A-Treffer"


def test_fallback_auf_zeilen_key_ohne_code(de):
    val = resolve(REL, BASE, "English#2", "", False)
    assert val == "Zeilen-Treffer"


def test_fallback_auf_zeilen_key_wenn_code_unbekannt(de):
    val = resolve(REL, BASE, "English#2", "CODE_UNBEKANNT", False)
    assert val == "Zeilen-Treffer"


def test_none_wird_durchgereicht_nicht_verwechselt(de):
    """None = absichtlich leer (kein Fallback, kein _MISSING)."""
    val = resolve(REL, BASE, "English#9", "CODE_NONE", False)
    assert val is None


def test_missing_wenn_kein_eintrag(de):
    val = resolve(REL, BASE, "English#99", "CODE_X", False)
    assert val is _MISSING


def test_missing_ohne_ctx_feld(de):
    assert resolve(REL, BASE, "keinkontext", "CODE_A", False) is _MISSING


def test_beta_root_nur_wenn_aktiv(de):
    assert resolve(REL, BASE, "English#1", "CODE_A", True) == "Beta-Treffer"
    assert resolve(REL, BASE, "English#1", "CODE_A", False) == "Code-A-Treffer"


def test_beta_root_verfaellt_auf_retail(de):
    """Nur im Beta gesetzter Code greift auch im Beta-Modus."""
    val = resolve(REL, BASE, "English#2", "", True)
    assert val == "Zeilen-Treffer"


def test_basename_root(de):
    val = resolve("unbekannt/Pfad.csvtxt", BASE, "English#1", "CODE_BASE", False)
    assert val == "Basenamen-Treffer"


def test_code_none_oder_leer_faellt_auf_zeilen_key(de):
    for code in (None, ""):
        assert resolve(REL, BASE, "English#2", code, False) == "Zeilen-Treffer"


def test_zeilen_key_mit_gleichem_code_existiert_nicht(de):
    """'r:'-Eintraege sind Zeilennummern, nicht Codes."""
    de.pop((REL, "English#r:2"))
    de[(REL, "English#r:CODE_A")] = "Falsch"
    assert resolve(REL, BASE, "English#2", "CODE_A", False) == "Code-A-Treffer"


def test_resolver_ignoriert_andere_felder(de):
    de[(REL, "Name#c:CODE_A")] = "Namens-Treffer"
    assert resolve(REL, BASE, "English#1", "CODE_A", False) == "Code-A-Treffer"


# --------------------------------------------------------------------------- #
# Tabellenladen (Registrierung)
# --------------------------------------------------------------------------- #


def test_load_tables_liefert_dict():
    de = apply_de.load_tables("de")
    assert isinstance(de, dict)
    assert len(de) > 0


def test_lade_technik_keine_nicht_tuple_keys():
    """Hilfsdaten (_FILES & Co.) duerfen nicht als Eintrag landen."""
    de = apply_de.load_tables("de")
    for key in de:
        assert isinstance(key, tuple) and len(key) == 2
        assert isinstance(key[0], str) and isinstance(key[1], str)


def test_echte_tabellen_auflösbar():
    """Smoke: ein bekannter Tabelleneintrag ist ueber resolve() erreichbar."""
    de = apply_de.load_tables("de")
    sample = next(k for k, v in de.items() if "#c:" in k[1] and v)
    rel, ctx = sample
    field, tagged = ctx.split("#", 1)
    code = tagged.split(":", 1)[1]
    base = rel.split("/")[-1].split(".")[0]
    assert resolve(rel, base, field + "#0", code, False) == de[sample]


# --------------------------------------------------------------------------- #
# _beta_active: Update-/Beta-Stand erkennen
# --------------------------------------------------------------------------- #


def test_beta_inactive_ohne_marker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert apply_de._beta_active(str(tmp_path / "po")) is False


def test_beta_active_ueber_work_marker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "work" / "Text" / "Text" / "Event" / "Miyako" / "Kamuhitsuki.csvtxt"
    marker.parent.mkdir(parents=True)
    marker.write_text("Code,English\r", encoding="utf-8")
    assert apply_de._beta_active(str(tmp_path / "po")) is True


def test_beta_active_ueber_po_marker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    po_root = tmp_path / "po"
    (po_root / "Text" / "Event" / "Miyako").mkdir(parents=True)
    (po_root / "Text" / "Event" / "Miyako" / "Kamuhitsuki.po").write_text(
        "", encoding="utf-8"
    )
    assert apply_de._beta_active(str(po_root)) is True
