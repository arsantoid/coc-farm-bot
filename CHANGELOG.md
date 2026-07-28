# Changelog

All notable changes to this project documented for AI agents and developers.

## [Unreleased]

### Fixed
- Zoom-out no longer uses broken `sendevent` ADB pinch (blocked by emulator virtual touch). Replaced with simple camera swipe to center.
- Deploy coords changed from extreme screen edges (80, 880) to around center `[(480,80), (480,420), (250,270), (710,270)]` to avoid hitting UI buttons at screen borders.

### Known
- Battle end detection not yet implemented — need to check for `end_battle.png`/`return_home.png` after all troops deployed.

## [2026-07-28]

### Added
- Emulator auto-detect: `detect_emulator_type()` detects BlueStacks/LDPlayer/MEmu via Windows tasklist
- `safe_shell()` wrapper: auto-reconnects ADB on "device offline" errors (63 shell calls wrapped)
- Cross-pattern ADB swipe zoom-out (later replaced with simple swipe)
- Edge-based deploy points `(80,200) to (880,440)` (later replaced with center ring)

### Fixed
- OpenCV OOM crash: set `OPENBLAS_NUM_THREADS` etc. to 1 before cv2 import
- `NoneType` screencap crash: null checks + `gc.collect()` in `find_template`
- ADB kill loop: removed `taskkill /f /im adb.exe`, scan ports instead
- Troop slot 0 skipped: `START_X=168→110`, `TOTAL_SLOTS=11→12`
- Spell drop wrong: coords changed from troop bar edge to village center (y<400)
- `start_bot.bat` pip fails: use `python -m pip`, check module `ppadb` not `pure-python-adb`
- Dynamic ADB path: use `USERPROFILE` env var

### Added (original codebase)
- Auto-farming loop (find match → deploy → surrender)
- Auto-upgrade buildings & lab
- Multi-account support via Supercell ID screen capture
- CoC crash recovery (reload button, force-close restart)
- Event popup cleanup
- Hero/siege/spell slot detection

## [Original] — ko9ma7/clash-of-clans-farm-bot

- Base bot by ko9ma7, designed for BlueStacks
- Uses OpenCV template matching + ADB shell commands
- Single account farm bot with zoom-out macro support
