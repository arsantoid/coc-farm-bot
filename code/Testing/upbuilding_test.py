"""
AUTO UPGRADE (TARGETED) - dengan Cancel Detection
==================================================
Detect building → klik → cek cancel (skip) / upgrade → confirm
"""

import cv2
import numpy as np
import os
import time
import random
import logging
from ppadb.client import Client as AdbClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")
DEBUG_DIR = os.path.join(BASE_DIR, "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'upgrade_test_log.txt'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi!")
    exit()
device = devices[0]
print(f"✅ Terhubung: {device.serial}")

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════
BUILDER_HEAD_X = 450
BUILDER_HEAD_Y = 25
CLOSE_X = 900
CLOSE_Y = 40

MENU_LEFT = 357
MENU_RIGHT = 620
MENU_TOP = 88
MENU_BOTTOM = 400

SCROLL_X = (MENU_LEFT + MENU_RIGHT) // 2
SCROLL_Y_TOP = MENU_TOP + 30
SCROLL_Y_BOTTOM = MENU_BOTTOM - 30

MENU_WAIT = 3.0
DETECT_THRESHOLD = 0.85
MAX_SCROLLS = 8
MAX_UPGRADES = 5

DELAY_AFTER_TAP = 1.5
DELAY_AFTER_CLOSE = 1.0
SCROLL_SPEED = 2000

# ═══════════════════════════════════════════════════════
# BUILDING TEMPLATES
# ═══════════════════════════════════════════════════════
BUILDING_TEMPLATES = [
    ("building_town_hall.png",           "Town Hall"),
    ("building_clan_castle.png",         "Clan Castle"),
    ("building_grand_warden.png",        "Grand Warden"),
    ("building_workshop.png",            "Workshop"),
    ("building_spell_factory.png",       "Spell Factory"),
    ("building_dark_spell_factory.png",  "Dark Spell Factory"),
    ("building_army_camp.png",           "Army Camp"),
    ("building_barracks.png",            "Barracks"),
    ("building_dark_barracks.png",       "Dark Barracks"),
    ("building_hero_hall.png",           "Hero Hall"),
    ("building_pet_house.png",           "Pet House"),
    ("building_blacksmith.png",          "Blacksmith"),
    ("building_builder_hut.png",         "Builder's Hut"),
    ("building_gold_mine.png",           "Gold Mine"),
    ("building_gold_storage.png",        "Gold Storage"),
    ("building_elixir_collector.png",    "Elixir Collector"),
    ("building_dark_elixir_drill.png",   "Dark Elixir Drill"),
    ("building_dark_elixir_storage.png", "Dark Elixir Storage"),
    ("building_barbarian_king.png",      "Barbarian King"),
    ("building_archer_queen.png",        "Archer Queen"),
    ("building_royal_champion.png",      "Royal Champion"),
    ("building_minion_prince.png",       "Minion Prince"),
    ("building_eagle_artillery.png",     "Eagle Artillery"),
    ("building_scattershhot.png",        "Scattershot"),
]

# UI templates
TEMPLATE_CONFIRM = os.path.join(GAMBAR_DIR, "confirm_text.png")
TEMPLATE_UPGRADE = os.path.join(GAMBAR_DIR, "upgrade_btn_dim.png")
TEMPLATE_BUSY = os.path.join(GAMBAR_DIR, "all_builders_busy.png")
TEMPLATE_HEADER = os.path.join(GAMBAR_DIR, "suggested_upgrades_text.png")
TEMPLATE_CANCEL = os.path.join(GAMBAR_DIR, "cancel_upgrade.png")  # ← BARU


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
def take_screenshot():
    screencap = device.screencap()
    return cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)


def find_on_screen(template_path, screen, threshold=0.85):
    """Find template di screen. Return (x, y, conf) atau None."""
    if not os.path.exists(template_path):
        return None
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return None
    th, tw = template.shape[:2]
    if th >= screen.shape[0] or tw >= screen.shape[1]:
        return None
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        cx = max_loc[0] + (tw // 2)
        cy = max_loc[1] + (th // 2)
        return (cx, cy, max_val)
    return None


def tap(x, y, offset=5):
    device.shell(f"input tap {x + random.randint(-offset, offset)} {y + random.randint(-offset, offset)}")


def scroll_down():
    device.shell(f"input swipe {SCROLL_X} {SCROLL_Y_BOTTOM} {SCROLL_X} {SCROLL_Y_TOP} {SCROLL_SPEED}")
    time.sleep(1.5)


def is_in_menu(x, y):
    return MENU_LEFT <= x <= MENU_RIGHT and MENU_TOP <= y <= MENU_BOTTOM


# ═══════════════════════════════════════════════════════
# SCAN MENU
# ═══════════════════════════════════════════════════════
def scan_buildings(screen):
    """Scan screen untuk cari building di menu. Return [(label, x, y, conf)]."""
    found = []
    for tpl_file, label in BUILDING_TEMPLATES:
        tpl_path = os.path.join(GAMBAR_DIR, tpl_file)
        pos = find_on_screen(tpl_path, screen, threshold=DETECT_THRESHOLD)
        if pos is None:
            continue
        cx, cy, conf = pos
        if is_in_menu(cx, cy):
            found.append((label, cx, cy, conf))
    return found


# ═══════════════════════════════════════════════════════
# UPGRADE ONE
# ═══════════════════════════════════════════════════════
def try_upgrade(label, x, y, conf):
    """Klik building → cek cancel → upgrade → confirm."""
    print(f"      [1] Klik {label} ({x}, {y}) conf={conf:.4f}")
    tap(x, y)
    time.sleep(DELAY_AFTER_TAP)

    screen = take_screenshot()

    # ── Cek Cancel (lagi di-upgrade) ──
    cancel = find_on_screen(TEMPLATE_CANCEL, screen, threshold=0.80)
    if cancel:
        print(f"      [CANCEL] {label} lagi di-upgrade! Skip.")
        logger.info(f"Skip (upgrading): {label}")
        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        return "cancel"

    # ── Cek Builders Busy ──
    busy = find_on_screen(TEMPLATE_BUSY, screen, threshold=0.85)
    if busy:
        print(f"      [BUSY] All builders busy!")
        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        return "busy"

    # ── Cari tombol Upgrade ──
    upgrade = find_on_screen(TEMPLATE_UPGRADE, screen, threshold=0.75)
    if not upgrade:
        print(f"      [SKIP] Tombol upgrade ga ketemu (max? resource kurang?)")
        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        return "skip"

    ux, uy, uconf = upgrade
    print(f"      [2] Upgrade ({ux}, {uy}) conf={uconf:.4f}")
    tap(ux, uy)
    time.sleep(DELAY_AFTER_TAP)

    # ── Cari Confirm ──
    screen = take_screenshot()
    confirm = find_on_screen(TEMPLATE_CONFIRM, screen, threshold=0.75)
    if not confirm:
        print(f"      [SKIP] Confirm ga muncul")
        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        return "skip"

    ccx, ccy, cconf = confirm
    print(f"      [3] Confirm ({ccx}, {ccy}) conf={cconf:.4f}")
    tap(ccx, ccy)
    time.sleep(DELAY_AFTER_TAP)

    # ── Cek busy setelah confirm ──
    screen = take_screenshot()
    busy = find_on_screen(TEMPLATE_BUSY, screen, threshold=0.85)
    if busy:
        print(f"      [BUSY] Builders busy setelah confirm!")
        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        return "busy"

    print(f"      ✅ {label} UPGRADED!")
    logger.info(f"Upgraded: {label}")
    return "upgraded"


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
def main():
    print()
    print("=" * 65)
    print("   AUTO UPGRADE (TARGETED)")
    print("=" * 65)

    # Cek template
    important = [TEMPLATE_CONFIRM, TEMPLATE_UPGRADE, TEMPLATE_BUSY, TEMPLATE_CANCEL]
    for tpl in important:
        name = os.path.basename(tpl)
        if not os.path.exists(tpl):
            print(f"   ⚠️ File ga ada: {name}")
    print()

    # ── Buka Builder Head ──
    print(f"[1] Buka Builder Head...")
    device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
    time.sleep(MENU_WAIT)

    total_upgraded = 0
    total_skipped = 0
    total_busy = 0
    total_cancel = 0
    upgraded_labels = set()
    cancel_labels = set()
    stop_reason = ""
    scroll_idx = 0

    for scroll_idx in range(MAX_SCROLLS + 1):
        if total_upgraded >= MAX_UPGRADES:
            stop_reason = f"Max upgrades ({MAX_UPGRADES})"
            break

        screen = take_screenshot()
        cv2.imwrite(os.path.join(DEBUG_DIR, f"upg_{scroll_idx}.png"), screen)

        # Cek header
        header = find_on_screen(TEMPLATE_HEADER, screen, threshold=0.50)
        if header is None and scroll_idx > 0:
            stop_reason = "Menu hilang"
            break

        # Scan
        buildings = scan_buildings(screen)
        new = [(l, x, y, c) for l, x, y, c in buildings
               if l not in upgraded_labels and l not in cancel_labels]

        print(f"\n   ╔═══ SCROLL {scroll_idx} {'═' * 45}")
        print(f"   ║ 📸 upg_{scroll_idx}.png")
        print(f"   ║ 🔍 {len(buildings)} detect, {len(new)} baru")

        for label, bx, by, bconf in new:
            if total_upgraded >= MAX_UPGRADES:
                break

            print(f"   ║")
            print(f"   ║ 🏠 {label} (conf={bconf:.4f})")

            result = try_upgrade(label, bx, by, bconf)

            if result == "upgraded":
                total_upgraded += 1
                upgraded_labels.add(label)
                device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
                time.sleep(MENU_WAIT)
                break  # break for, restart scan dari atas

            elif result == "cancel":
                total_cancel += 1
                cancel_labels.add(label)
                # Refresh scan di posisi scroll yang sama
                break

            elif result == "busy":
                total_busy += 1
                stop_reason = "Builders busy"
                break

            elif result == "skip":
                total_skipped += 1
                upgraded_labels.add(label)
                device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
                time.sleep(MENU_WAIT)
                break

        if stop_reason:
            break

        if len(new) == 0:
            print(f"   ║ ℹ️ Semua udah di-skip/upgrade/cancel")

        print(f"   ║ 📜 Scroll down...")
        print(f"   ╚{'═' * 60}")
        scroll_down()

    # ── Summary ──
    print()
    print("=" * 65)
    print("   UPGRADE SUMMARY")
    print("=" * 65)
    print(f"   ✅ Upgraded  : {total_upgraded}")
    print(f"   ⏭️ Skipped   : {total_skipped}")
    print(f"   🚫 Cancel   : {total_cancel}")
    print(f"   🔴 Busy     : {total_busy}")
    if stop_reason:
        print(f"   🛑 Stop     : {stop_reason}")
    if upgraded_labels:
        print(f"   🏠 Upgraded : {', '.join(upgraded_labels)}")
    if cancel_labels:
        print(f"   ⏸️ Upgrading: {', '.join(cancel_labels)}")
    print()

    tap(CLOSE_X, CLOSE_Y)
    print("   ✅ SELESAI!")


if __name__ == "__main__":
    main()