# AGENTS.md — CoC Farm Bot

## Project Overview
Auto-farming bot for Clash of Clans via ADB + OpenCV template matching. Runs on BlueStacks or LDPlayer emulator. Visual-only approach (no Supercell API), single emulator multi-account via Supercell ID switching.

## Architecture

```
bot_farm_auto_v4.py    → Main bot loop
reconnect_adb.py        → ADB connection helper
auto_scan_accounts.py   → EasyOCR account scanner
start_bot.bat           → Windows launcher
Gambar/                 → Template images (troop, building, UI)
debug/                  → Screenshot debug dumps
```

### Flow
1. Launch emulator → Connect ADB → Launch CoC app
2. Detect current account from Supercell ID switch screen
3. Village loop: collect resources, check storage, upgrade buildings/lab
4. Battle loop: find match → deploy troops → wait for battle end → return home
5. If max accounts reached, loop back to first account

## Key Coordinates System

```
Screen: 960 x 540 (emulated)
Troop bar: y=495, START_X=110, GAP_X=58, TOTAL_SLOTS=12
Village center: (480, 270)
Deploy points: [(480,80), (480,420), (250,270), (710,270)] — around center
Spell drop: center village area, y<400
```

## Critical Patches (solved problems)

### 1. OpenCV OOM Crash
**Root cause:** OpenCV 5.0.0 spawns many threads causing memory alloc failure.
**Fix:** Set env vars before import:
```python
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
```

### 2. ADB Device Offline Mid-Operation
**Root cause:** BlueStacks ADB restarts (HD-Adb.exe) killing connection.
**Fix:** `safe_shell()` wrapper — catch "offline" in exception, call `reconnect_adb.reconnect()`, retry 3x.
**NEVER** kill adb.exe or HD-Adb.exe. Connect ppadb directly to port.

### 3. ADB Kill Loop with BlueStacks
**Root cause:** Old bot killed all adb processes, BlueStacks auto-restarts ADB infinitely.
**Fix:** Removed `taskkill /f /im adb.exe`. Scan ports 5555-5569 for existing device.

### 4. Troop Slot 0 Skipped
**Root cause:** START_X=168, SLOT_W=58 → slot 0 (x=110) was never selected.
**Fix:** Changed START_X=110, TOTAL_SLOTS=12.

### 5. Spell Drop at Village Center
**Root cause:** Old coords tapped troop bar edge instead of center.
**Fix:** `SPELL_COORDS_1`/`SPELL_COORDS_2` all have y<400, around (480, 270).

### 6. Zoom Out Failure (ADB pinch blocked)
**Root cause:** Emulator virtual touch (event4) differs between BlueStacks/LDPlayer versions.
**Current fix:** Skip zoom-out entirely. Use camera swipe to center base.
**Known issue:** If deploy lands on red zone (during battle), troops won't spawn. The deploy coords are placed around center of screen to avoid UI borders.

### 7. Emulator Auto-Detect
Detects BlueStacks (HD-Player.exe), LDPlayer (dnplayer.exe), MEmu via tasklist on startup.

## Known Issues / Future Work

| Issue | Priority | Notes |
|-------|----------|-------|
| Zoom-out unreliable across emulators | HIGH | ADB pinch(sendevent) or macro per emulator |
| Battle end detection not implemented | HIGH | Need to detect end_battle.png / return_home.png after full deploy |
| Hero ability timing | MEDIUM | Currently hardcoded delay, could use OCR for ability icon |
| Event troops deploy logic | MEDIUM | event_troop_defs needs update per season |
| No shield/guard detection | LOW | Bot will attack while guard active, wasting army |

## ADB Port Mapping

| Emulator | Default ADB Port |
|----------|-----------------|
| LDPlayer | 5555 |
| BlueStacks | 5556 or 5565 |
| MEmu | 21503 |

Bot scans 5555-5569 sequentially.

## Distribution

- GitHub: `arsantoid/coc-farm-bot` (public)
- `start_bot.bat` auto-installs Python deps (no portable python yet)
- Requirements: `opencv-python>=4.8.0`, `numpy>=1.24.0`, `pure-python-adb`

## For New AI Agents

When continuing this project:
1. Read this file first (AGENTS.md) for architecture context
2. Read CHANGELOG.md for recent changes
3. Check `bot_farm_auto_v4.py` comments for labeled sections
4. The `debug/` folder has timestamped screenshots with issue context
5. If adding new template images, put in `Gambar/` folder with descriptive name
6. Template matching uses OpenCV `matchTemplate` with TM_CCOEFF_NORMED
