# Changelog

All notable changes to **sakuna-translation-patch** are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-11-05

First public release. Complete German translation for retail *and* OpenBeta,
with an update-proof table schema.

### Added
- **Code-based table keys** (`migrate_keys.py`): every translation is keyed by
  the row's stable `Code` cell (`English#c:CODE`) instead of its row index.
  Shifted or inserted rows in game updates keep their translations automatically;
  genuinely new rows surface in `apply_de`'s missing report instead of being
  mis-assigned. 39 rows without a unique code keep row keys (`#r:N`).
- **OpenBeta coverage** — 2105 additional entries in batches β1–β6, registered
  under the `#beta` root so retail builds stay byte-identical.
  Beta builds: `Text.arc` = `cfa6d23f3dbaa42c`, `Common.arc` = `97c25a8e1af739c9`
  (10231 entries verified, 0 mismatches).
- **Test suite** (`tests/`, 86 pytest cases) covering the historical regression
  points: code/row key resolution, PO read/write roundtrip including escaping
  and `#:` code comments, the `CSV_EXTENSIONS` list (the `.csvtr` omission),
  CR-only row splitting, `csv_to_po`/`po_to_csv` roundtrip, and `validate_csv`.
  Run with `python -m pytest` (deps: `pip install -r requirements-dev.txt`).
- `tables/<lang>/` language directory layout: adding a language means dropping
  in a folder, no code changes.
- `install.py --status` and `--version`.

### Changed
- `apply_de.resolve()` performs the lookup: `[#beta-root] × [path, basename] ×
  [code key, row key]`. No rebase pass and no marker-guard mask any more —
  the code keys protect themselves.
- `verify_build.py` uses the same resolver.
- Translation tables moved to `tables/de/` and `tables/de/beta/`
  (77 files, 10377 entries).

### Removed
- `make_rebase.py` and `de_rebase.py` (8008-line rebase table) — superseded by
  code keys.
- Marker-guard mask in `install.py` (no longer needed).

### Fixed
- `CSV_EXTENSIONS` now lists every translatable suffix, including `.csvtr`.
  Before this, `po-dir` silently skipped all 18 Travel files on a fresh install.
- Version-diff row counting splits rows only on `\r` (cells contain real `\n`).

## [1.1.0] — 2026-11-05

OpenBeta support and content.

### Added
- Rebase support for game updates / OpenBeta with pristine source protection:
  the installer always builds from an untouched retail extract.
- `#beta` table lookup and `verify_build.py` verification gate.
- Six translation batches β1–β6: 7 new dialogue files plus UI/Param
  (409 + 417 + 268 + 240 + 399 + 373 = 2105 entries).

## [1.0.0] — 2026-11-05

Initial release.

### Added
- Full German translation of the retail game: **8196 strings**
  (`Text.arc` 5734 of 5773 = 99.3 %, `Common.arc` 2462) in 52 tables.
- Toolchain: `sakuna.py` (ARC read/write as TGP0 + LZ4, CSV↔PO, validation),
  `apply_de.py` (table injection), `verify_build.py`.
- **One-command installer** `install.py` with `INSTALL.bat` / `RESTORE.bat`:
  game-path discovery (Steam, GOG, Flatpak, Proton, Windows registry),
  automatic `lz4` install, one-time `.bak-original` backups, build from the
  player's own copy, `"Language": "Sp"` switch, `--restore`.
  Cross-platform: Windows, Linux, macOS.
- Bilingual player-first README (English + German) with FAQ and troubleshooting.
- Legal safety: no game data in the repository — only the toolchain and the
  German tables. The `.arc` archives are built locally from the user's own copy.

[2.0.0]: https://github.com/zachelnet/sakuna-translation-patch/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/zachelnet/sakuna-translation-patch/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/zachelnet/sakuna-translation-patch/releases/tag/v1.0.0
