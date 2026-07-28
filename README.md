# Clash of Clans Farm Bot

Auto-farming bot for Clash of Clans that runs on BlueStacks or LDPlayer emulator. Features include:

- **Auto-detect ADB & Emulator** - Supports both BlueStacks and LDPlayer
- **Multi-account Support** - Switch between Supercell ID accounts automatically
- **Full Farming Loop** - Find match, deploy troops, surrender, repeat
- **Auto Upgrade** - Building and Lab upgrades
- **Smart Troop Detection** - Automatically detects troop slots and types
- **Crash Recovery** - Auto-restarts CoC if it crashes

## Prerequisites

1. **Emulator**: BlueStacks or LDPlayer installed and running
2. **Clash of Clans**: Installed on the emulator with Supercell ID logged in
3. **Python 3.9+**: [Download from python.org](https://python.org) (Check "Add to PATH" during install)

## Quick Start

1. Download this repository
2. Double-click **`start_bot.bat`**
3. The script will automatically:
   - Check for Python and install dependencies if missing
   - Download ADB if not present
   - Connect to your emulator
   - Start the bot

## Manual Setup

If the automatic setup fails, install dependencies manually:

```bash
pip install -r requirements.txt
```

Download Android Platform Tools and extract to your user folder:
- Windows: https://developer.android.com/studio/releases/platform-tools

## Configuration

Edit `code/bot_farm_auto_v4.py` to configure your accounts:

```python
DAFTAR_AKUN = [
    ("scid_example.png", "example"),  # (screenshot_filename, account_name)
    ("scid_account2.png", "account2"),
]
```

## Troubleshooting

**Bot can't find ADB:**
- Ensure `platform-tools` folder is in your user directory (`C:\Users\YourName\platform-tools\`)
- Or install Android SDK Platform Tools

**Bot can't connect to emulator:**
- Make sure the emulator is running
- Try restarting the emulator

**CoC crashes frequently:**
- LDPlayer users: Try switching network mode from NAT to Bridged in settings
- BlueStacks users: Disable "ADB debugging" in settings to prevent conflicts
