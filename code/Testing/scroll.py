"""
TEST SCROLL: Cek scroll di menu Builder Head
=============================================
1. Jalankan script
2. Script buka menu, terus scroll pelan-pelan
3. Screenshot tiap posisi scroll
"""

import cv2
import numpy as np
import os
import time
from ppadb.client import Client as AdbClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")
DEBUG_DIR = os.path.join(BASE_DIR, "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi!")
    exit()
device = devices[0]
print(f"✅ Terhubung: {device.serial}")

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

def take_screenshot():
    screencap = device.screencap()
    return cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

def scroll_down(speed=1200):
    """Scroll menu ke bawah (lihat item berikutnya)."""
    device.shell(f"input swipe {SCROLL_X} {SCROLL_Y_BOTTOM} {SCROLL_X} {SCROLL_Y_TOP} {speed}")
    time.sleep(1.5)

def scroll_up(speed=1200):
    """Scroll menu ke atas (lihat item sebelumnya)."""
    device.shell(f"input swipe {SCROLL_X} {SCROLL_Y_TOP} {SCROLL_X} {SCROLL_Y_BOTTOM} {speed}")
    time.sleep(1.5)


def main():
    print()
    print("=" * 60)
    print("   TEST SCROLL MENU")
    print("=" * 60)
    print(f"   Menu: X({MENU_LEFT}-{MENU_RIGHT}) Y({MENU_TOP}-{MENU_BOTTOM})")
    print(f"   Scroll center: ({SCROLL_X}, {SCROLL_Y_TOP}) → ({SCROLL_X}, {SCROLL_Y_BOTTOM})")
    print()

    # ── Pilih speed ──
    print("   Pilih scroll speed:")
    print("   [1] Lambat  (2000ms)")
    print("   [2] Sedang  (1200ms)")
    print("   [3] Cepat   (600ms)")
    pilih = input("   > ").strip()
    speed = {"1": 2000, "2": 1200, "3": 600}.get(pilih, 1200)
    print(f"   Speed: {speed}ms")
    print()

    # ── Buka menu ──
    input("   Tekan ENTER untuk buka Builder Head...")
    device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
    time.sleep(3.0)

    # ── Screenshot awal ──
    screen = take_screenshot()
    cv2.imwrite(os.path.join(DEBUG_DIR, "scroll_test_0.png"), screen)
    print(f"   [0] 📸 scroll_test_0.png (posisi awal)")

    # ── Scroll down ──
    print()
    print("   SCROLL DOWN:")
    max_down = input("   Berapa kali scroll down? (default 5): ").strip()
    max_down = int(max_down) if max_down.isdigit() else 5

    for i in range(max_down):
        input(f"   Tekan ENTER untuk scroll down ke-{i+1}...")
        scroll_down(speed)

        screen = take_screenshot()
        fname = f"scroll_test_down_{i+1}.png"
        cv2.imwrite(os.path.join(DEBUG_DIR, fname), screen)
        print(f"   [{i+1}] 📸 {fname}")

    # ── Scroll up balik ──
    print()
    back = input("   Scroll balik ke atas? (y/n): ").strip().lower()
    if back == "y":
        print("   SCROLL UP:")
        for i in range(max_down):
            input(f"   Tekan ENTER untuk scroll up ke-{i+1}...")
            scroll_up(speed)

            screen = take_screenshot()
            fname = f"scroll_test_up_{i+1}.png"
            cv2.imwrite(os.path.join(DEBUG_DIR, fname), screen)
            print(f"   [{i+1}] 📸 {fname}")

    # ── Tutup ──
    print()
    close = input("   Tutup menu? (y/n): ").strip().lower()
    if close == "y":
        device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
        print("   ✅ Menu ditutup.")

    print()
    print(f"   Cek folder debug/ untuk semua screenshot scroll_test_*.png")
    print("   SELESAI!")


if __name__ == "__main__":
    main()