# Screenshot shot list

All four screenshots in this folder are real in-game captures
(2026-11-07), cropped to the game's 2560×1440 render area — 440 px of
black bars removed left and right.

Replace a file in place and the README picks it up automatically; no
markup changes needed. Keep the filenames.

## What is in place

| File | Content | Source |
|---|---|---|
| `ingame-german.png` | Village scene, Sakuna speech bubble with name plate („Der Zehnttag ist so langweilig…") | `12-03-06` |
| `ingame-ui.png` | Status screen — Stufe 19, LP, Sättigung, Stärke/Vitalität/Magie/Glück, Reis-Info | `12-05-00` |
| `worldmap-umlauts.png` | World map: Hügel des Hasennests, Reißzähne, Zylindrische Höhle, Sprungsteinhügel; HUD „Sammler losschicken", „Erkundungsstufe" | `12-09-05` |
| `ingame-beta.png` | OpenBeta banquet in the Lofty Realm with Tama | `12-04-11` |

Each was chosen for a specific proof point: dialogue rendering, complete
UI coverage, font glyph coverage (ä/ö/ü/ß — the classic fan-translation
failure mode), and the 2105 β entries actually appearing in game.

## Not included on purpose

- **Installer window** — the install is a three-step terminal script and
  screenshots of it add little. The README describes it instead.
- **Options/title menu** — the status screen already demonstrates UI
  coverage. Alternates are listed below.

## Taking new ones

```bash
# finds the Sakuna window, crops to 3840x2160, writes docs/<name>.png
python3 capture.py <name>          # e.g. python3 capture.py dialog
python3 capture.py <name> --look   # preview into /tmp, don't save
```

Source material from the last capture run is kept outside the repo in
`~/Bilder/Bildschirmfotos/sakuna/`. Unreleased alternates (cropped, ready
to swap in): `12-03-10/14/25/47` (more dialogue lines, one subtitle-style),
`12-05-05/09/23/31`, and the main menu `Starten/Fortsetzen/Optionen/Beenden`.
