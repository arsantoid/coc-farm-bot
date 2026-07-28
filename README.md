# Clash of Clans Farm Bot

Auto-farming bot for Clash of Clans on BlueStacks or LDPlayer emulator via ADB + OpenCV.

- Auto-detect ADB & Emulator (BlueStacks/LDPlayer/MEmu)
- Multi-account via Supercell ID
- Full farm loop: find match, deploy, surrender
- Auto-upgrade buildings & lab
- Crash recovery

## Quick Start

1. Clone/download repo
2. Install Python 3.9+ (add to PATH)
3. Run `start_bot.bat`

## Configuration

Edit `DAFTAR_AKUN` in `code/bot_farm_auto_v4.py`:

```python
DAFTAR_AKUN = [
    ("scid_example.png", "example"),
    ("scid_account2.png", "account2"),
]
```

## Docs for AI Agents

- [AGENTS.md](AGENTS.md) — Architecture, coords, solved problems
- [CHANGELOG.md](CHANGELOG.md) — Full patch history

## Disclaimer

Educational only. Use at your own risk. Supercell ToS prohibit automation.
