#!/usr/bin/env python3
"""Trägt alle deutschen Strings in alle .po-Dateien unter po/ ein.

Lookup pro Eintrag:
  1. (voller Archivpfad, msgctxt)   - fuer Dateien mit doppeltem Namen
  2. (Dateiname ohne Endung, msgctxt) - fuer die aelten Tabellen

Fehlt beides, wird der Eintrag unveraendert gelassen und gemeldet.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sakuna as S
from de_option_title_system import DE as DE_A
from de_game import DE_GAME as DE_B
from de_place import DE_PLACE as DE_C
from de_pause_save_common import DE_PAUSE, DE_SAVELOAD, DE_COMMON
from de_worldmap_tanbo import DE_WORLDMAP, DE_TANBO
from de_soilwork import DE_SOILWORK
from de_short_events import DE_SHORT
from de_charactername import DE_CHARNAME
from de_skills_param import DE_SKILL_ATTACK, DE_SKILL_SOILWORK
from de_weapon import DE_WEAPON
from de_armor import DE_ARMOR
from de_mura_small import DE_MURA
from de_mura_batch2 import DE_MURA2
from de_mura_batch3 import DE_MURA3
from de_mura_batch4 import DE_MURA4
from de_mura_batch5 import DE_MURA5
from de_soto_eventmain_a import DE_SOTO_EM_1
from de_soto_eventmain_b import DE_SOTO_EM_2
from de_soto_eventsub import DE_SOTO_ES
from de_soto_kinta import DE_SOTO_KINTA
from de_ima_mirthe import DE_IMA_MIRTHE
from de_imaonly_eventmain import DE_IMAONLY_EM
from de_mura_yui_dojo import DE_YUI, DE_DOJO_ES
from de_soto_yui import DE_SOTO_YUI
from de_soto_mirthe import DE_SOTO_MIRTHE
from de_dinner_a import DE_DINNER_1
from de_dinner_b import DE_DINNER_2
from de_dinner_c import DE_DINNER_3A
from de_dinner_d import DE_DINNER_3B
from de_ima_eventmain import DE_IMA_EM
from de_soto_tauemon import DE_SOTO_TAUEMON
from de_soto_kaimaru import DE_SOTO_KAIMARU
from de_event_small_a import DE_EVT_A
from de_event_small_b import DE_EVT_B
from de_event_small_c import DE_EVT_C
from de_travel import DE_TRAVEL
from de_evt_rest_a1 import DE_REST_A1
from de_evt_rest_a2 import DE_REST_A2
from de_evt_rest_a3 import DE_REST_A3
from de_evt_rest_b1 import DE_REST_B1
from de_evt_rest_b2 import DE_REST_B2
from de_evt_rest_b3 import DE_REST_B3
from de_evt_rest_c1 import DE_REST_C1
from de_evt_rest_c2 import DE_REST_C2
from de_quest import DE_QUEST
from de_achievement_material import DE_ACHIEVEMENT, DE_MATERIAL
from de_enchant import DE_ENCHANT
from de_food import DE_FOOD
from de_keyitem import DE_KEYITEM
from de_cooking import DE_COOKING
from de_worldmap_landmark import DE_WORLDMAP_LM
from de_credits import DE_CREDITS

DE = {}
for table in (DE_A, DE_B, DE_C, DE_PAUSE, DE_SAVELOAD, DE_COMMON,
              DE_WORLDMAP, DE_TANBO, DE_SOILWORK, DE_SHORT,
              DE_CHARNAME, DE_SKILL_ATTACK, DE_SKILL_SOILWORK, DE_WEAPON, DE_ARMOR,
              DE_MURA, DE_MURA2, DE_MURA3, DE_MURA4, DE_MURA5,
              DE_SOTO_EM_1, DE_SOTO_EM_2, DE_SOTO_ES, DE_SOTO_KINTA,
              DE_IMA_MIRTHE, DE_IMAONLY_EM, DE_YUI, DE_DOJO_ES,
              DE_SOTO_YUI, DE_SOTO_MIRTHE, DE_DINNER_1, DE_DINNER_2, DE_DINNER_3A, DE_DINNER_3B,
              DE_IMA_EM, DE_SOTO_TAUEMON, DE_SOTO_KAIMARU,
              DE_EVT_A, DE_EVT_B, DE_EVT_C, DE_TRAVEL,
              DE_REST_A1, DE_REST_A2, DE_REST_A3,
              DE_REST_B1, DE_REST_B2, DE_REST_B3,
              DE_REST_C1, DE_REST_C2,
              DE_QUEST, DE_ACHIEVEMENT, DE_MATERIAL,
              DE_ENCHANT, DE_FOOD, DE_KEYITEM,
              DE_COOKING, DE_WORLDMAP_LM, DE_CREDITS):
    for _k, _v in table.items():
        if _k in DE and DE[_k] != _v:
            print(f"WARNUNG: doppelter Tabellen-Schluessel, Wert wird ueberschrieben: {_k!r}")
        DE[_k] = _v

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
            fh.write(f'msgctxt "{S._po_escape(e["msgctxt"])}"\n')
            fh.write(f'msgid "{S._po_escape(e["msgid"])}"\n')
            fh.write(f'msgstr "{S._po_escape(e["msgstr"])}"\n\n')


def main(po_root: str = "po") -> int:
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
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "po"))
