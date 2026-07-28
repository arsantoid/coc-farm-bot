"""
Auto-scan Supercell ID accounts from Switch Account screen.

Flow:
1. Open Settings → Switch Account
2. Screenshot the account list
3. EasyOCR reads all names
4. Auto-crop each entry, save as scid_[name].png
5. Update DAFTAR_AKUN in bot_farm_auto_v4.py

Usage:
    python auto_scan_accounts.py          # Interactive (needs ADB + CoC)
    python auto_scan_accounts.py --test   # Test OCR on existing screenshot
"""
import sys
import os
import time
import subprocess
import cv2
import numpy as np

# Paths
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
GAMBAR_DIR = os.path.join(os.path.dirname(BOT_DIR), "Gambar")
BOT_FILE = os.path.join(BOT_DIR, "bot_farm_auto_v4.py")
ADB = r"C:\Users\Administrator\platform-tools\adb.exe"
DEVICE = "127.0.0.1:5556"
SCREENSHOT_PATH = os.path.join(GAMBAR_DIR, "switch_account_screen.png")


def adb_cmd(cmd):
    """Run ADB command, return output."""
    full = [ADB, "-s", DEVICE] + cmd.split()
    r = subprocess.run(full, capture_output=True, text=True, timeout=10)
    return r.stdout.strip()


def adb_shell(cmd):
    """Run ADB shell command."""
    return adb_cmd(f"shell {cmd}")


def screenshot():
    """Take screenshot via ADB, return numpy image (BGR)."""
    raw = subprocess.run(
        [ADB, "-s", DEVICE, "exec-out", "screencap", "-p"],
        capture_output=True, timeout=10
    ).stdout
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def navigate_to_switch_account():
    """Navigate CoC to Settings → Switch Account screen."""
    # Make sure we're in CoC
    focus = adb_shell("dumpsys window | grep mCurrentFocus")
    if "clashofclans" not in focus:
        print("❌ CoC not running! Launching...")
        adb_shell("monkey -p com.supercell.clashofclans -c android.intent.category.LAUNCHER 1")
        time.sleep(8)

    # Close any popups first
    for _ in range(3):
        adb_shell("input keyevent 4")
        time.sleep(1)

    # Open Settings
    print("🔧 Opening Settings...")
    # Settings gear is typically at bottom-left of home screen
    # Use template match to find it
    from ppadb.client import Client as AdbClient
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    if not devices:
        print("❌ No ADB device!")
        return False

    device = devices[0]

    # Take screenshot and find settings_gear.png
    img = screenshot()
    settings_tpl = cv2.imread(os.path.join(GAMBAR_DIR, "settings_gear.png"))
    if settings_tpl is not None:
        result = cv2.matchTemplate(img, settings_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.80:
            h, w = settings_tpl.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            adb_shell(f"input tap {cx} {cy}")
            print(f"   ✅ Settings tapped ({cx}, {cy}), conf={max_val:.2f}")
            time.sleep(2)
        else:
            print(f"   ⚠️ Settings gear not found (best={max_val:.2f}), tapping default position")
            adb_shell("input tap 70 490")  # Default position for settings gear
            time.sleep(2)
    else:
        print("   ⚠️ settings_gear.png not found, tapping default position")
        adb_shell("input tap 70 490")
        time.sleep(2)

    # Tap Supercell ID / Switch Account button
    print("📋 Looking for Switch Account / Supercell ID button...")
    img = screenshot()
    switch_tpl = cv2.imread(os.path.join(GAMBAR_DIR, "switch_account.png"))
    if switch_tpl is not None:
        result = cv2.matchTemplate(img, switch_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.75:
            h, w = switch_tpl.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            adb_shell(f"input tap {cx} {cy}")
            print(f"   ✅ Switch Account tapped ({cx}, {cy}), conf={max_val:.2f}")
            time.sleep(3)
        else:
            print(f"   ⚠️ switch_account.png not found (best={max_val:.2f})")
            # Try tapping Supercell ID button area (usually top-left in settings)
            adb_shell("input tap 200 130")
            time.sleep(3)
    else:
        # Try text-based: look for "Supercell ID" text
        adb_shell("input tap 200 130")
        time.sleep(3)

    # Now we should be on Switch Account screen
    # Take screenshot for OCR
    print("📸 Taking screenshot of account list...")
    img = screenshot()
    cv2.imwrite(SCREENSHOT_PATH, img)
    print(f"   ✅ Saved: {SCREENSHOT_PATH}")
    return True


def ocr_account_names(img_path=None):
    """OCR the switch account screen, return list of (name, y_position, crop_region)."""
    import easyocr

    if img_path is None:
        img_path = SCREENSHOT_PATH

    img = cv2.imread(img_path)
    if img is None:
        print(f"❌ Cannot read: {img_path}")
        return []

    h, w = img.shape[:2]
    print(f"📐 Screen: {w}x{h}")

    # OCR the full image
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(img_path)

    print(f"\n🔍 OCR found {len(results)} text blocks:")
    names = []
    for bbox, text, conf in results:
        # bbox is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        x1 = int(bbox[0][0])
        y1 = int(bbox[0][1])
        x2 = int(bbox[2][0])
        y2 = int(bbox[2][1])
        cy = (y1 + y2) // 2

        print(f"   [{x1},{y1}-{x2},{y2}] conf={conf:.2f} → \"{text}\"")

        # Filter: account names are typically
        # - In the middle/right area of screen (x > 150)
        # - Not too long (< 25 chars)
        # - Not UI elements like "Switch", "Connected", "Log Out"
        skip_words = ["switch", "account", "connected", "log out", "settings",
                       "cancel", "confirm", "back", "supercell", "id",
                       "loading", "google", "play", "game", "center",
                       "facebook", "email", "enter", "submit"]
        text_lower = text.lower().strip()

        if any(sw in text_lower for sw in skip_words):
            continue
        if len(text.strip()) < 2 or len(text.strip()) > 25:
            continue
        if x1 < 100:  # Too far left = UI element
            continue

        names.append({
            'name': text.strip(),
            'y_center': cy,
            'bbox': (x1, y1, x2, y2),
            'conf': conf
        })

    # Sort by y position (top to bottom)
    names.sort(key=lambda n: n['y_center'])

    # Deduplicate: if two names are very close vertically (< 20px), keep higher conf
    deduped = []
    for n in names:
        if deduped and abs(n['y_center'] - deduped[-1]['y_center']) < 20:
            if n['conf'] > deduped[-1]['conf']:
                deduped[-1] = n
        else:
            deduped.append(n)

    print(f"\n✅ Filtered account names: {len(deduped)}")
    for i, n in enumerate(deduped):
        print(f"   [{i+1}] \"{n['name']}\" (y={n['y_center']}, conf={n['conf']:.2f})")

    return deduped


def crop_and_save_accounts(names, img_path=None):
    """Crop each account entry from screenshot, save as scid_[name].png."""
    if img_path is None:
        img_path = SCREENSHOT_PATH

    img = cv2.imread(img_path)
    h, w = img.shape[:2]

    # Each account entry in the list takes about 60-80px height
    # Crop region: centered on y_center, with some padding
    saved = []
    for i, n in enumerate(names):
        cy = n['y_center']
        name = n['name']

        # Sanitize filename
        safe_name = name.lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

        # Crop: full width, centered vertically
        crop_top = max(0, cy - 35)
        crop_bottom = min(h, cy + 35)
        crop = img[crop_top:crop_bottom, :]

        # Save
        filename = f"scid_{safe_name}.png"
        filepath = os.path.join(GAMBAR_DIR, filename)
        cv2.imwrite(filepath, crop)
        print(f"   💾 [{i+1}] {filename} ({w}x{crop_bottom - crop_top})")
        saved.append((filename, name))

    return saved


def update_bot_config(saved_accounts):
    """Update DAFTAR_AKUN in bot_farm_auto_v4.py."""
    with open(BOT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Build new DAFTAR_AKUN
    entries = []
    for filename, name in saved_accounts:
        safe_name = name.lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        # Also save full name for readability
        entries.append(f'    ("{filename}",    "{safe_name}"),')

    new_dafar = "DAFTAR_AKUN = [\n" + "\n".join(entries) + "\n]"

    # Replace existing DAFTAR_AKUN block
    import re
    pattern = r"DAFTAR_AKUN = \[.*?\]"
    new_content = re.sub(pattern, new_dafar, content, flags=re.DOTALL)

    with open(BOT_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n✅ Updated DAFTAR_AKUN in bot_farm_auto_v4.py ({len(saved_accounts)} accounts)")


def run_full_scan():
    """Full auto-scan: navigate → screenshot → OCR → crop → update config."""
    print("=" * 55)
    print("   AUTO-SCAN SUPERCELL ID ACCOUNTS")
    print("=" * 55)

    # Step 1: Navigate to Switch Account screen
    print("\n[1/4] Navigating to Switch Account screen...")
    if not navigate_to_switch_account():
        return False

    # Step 2: OCR
    print("\n[2/4] OCR reading account names...")
    names = ocr_account_names()
    if not names:
        print("❌ No account names found! Screen might not be on Switch Account list.")
        print("   Make sure CoC is showing the Supercell ID Switch Account screen.")
        return False

    # Step 3: Crop & save
    print("\n[3/4] Cropping and saving templates...")
    saved = crop_and_save_accounts(names)

    # Step 4: Update bot config
    print("\n[4/4] Updating bot config...")
    update_bot_config(saved)

    # Done
    print("\n" + "=" * 55)
    print("   ✅ SCAN COMPLETE!")
    print(f"   📁 Templates: {GAMBAR_DIR}")
    print(f"   📝 Bot config updated: {len(saved)} accounts")
    print("=" * 55)

    # Print summary
    print("\nAccounts found:")
    for i, (fn, name) in enumerate(saved):
        print(f"  [{i}] {name} → {fn}")

    return True


def run_test():
    """Test OCR on existing screenshot."""
    print("🧪 Testing OCR on existing screenshot...")

    if not os.path.exists(SCREENSHOT_PATH):
        print(f"❌ No screenshot found: {SCREENSHOT_PATH}")
        print("   Run without --test first to capture one.")
        return

    names = ocr_account_names(SCREENSHOT_PATH)
    if names:
        print("\nWould save these templates:")
        saved = crop_and_save_accounts(names, SCREENSHOT_PATH)
        print(f"\n{len(saved)} templates ready. Run without --test to update bot config.")
    else:
        print("No account names found in screenshot.")


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test()
    else:
        run_full_scan()
