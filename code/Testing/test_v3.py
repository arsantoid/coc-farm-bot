# ==========================================
# TEST_SLOT_V5.py — Hybrid detection
# Jalankan saat masuk battle
# ==========================================
import cv2
import numpy as np
from ppadb.client import Client as AdbClient
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
device = devices[0]

empty_path = os.path.join(GAMBAR_DIR, "empty_slot.png")
empty_template = cv2.imread(empty_path, cv2.IMREAD_COLOR)

if empty_template is None:
    print("❌ empty_slot.png tidak ditemukan!")
    exit()

tw = empty_template.shape[1]
START_X = 168
GAP_X = 58
TOTAL_SLOTS = 11
TAP_Y = 495

print(f"✅ Template: {tw}x{empty_template.shape[0]}")
print(f"✅ Grid: start={START_X}, gap={GAP_X}, slots={TOTAL_SLOTS}")

screencap = device.screencap()
screen = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
result = cv2.matchTemplate(screen, empty_template, cv2.TM_CCOEFF_NORMED)

print()
print(f"   {'#':<4} {'X':<6} {'sim':<8} {'Var':<6} {'R':<5} {'G':<5} {'B':<5} {'Status'}")
print("   " + "-" * 55)

slots = []
for i in range(TOTAL_SLOTS):
    slot_x = START_X + (i * GAP_X)

    # === CHECK 1: Template matching ===
    x1 = max(0, slot_x)
    x2 = min(result.shape[1], slot_x + tw)
    area = result[:, x1:x2]
    max_sim = float(np.max(area))

    # === CHECK 2: Pixel analysis di tengah slot ===
    # Cek beberapa titik di tengah slot
    cx = slot_x + (tw // 2)
    points = []
    for dy in [-10, 0, 10]:
        py = TAP_Y + dy
        px = min(cx, screen.shape[1] - 1)
        py = min(max(py, 0), screen.shape[0] - 1)
        b, g, r = screen[py, px]
        points.append((int(r), int(g), int(b)))

    avg_r = sum(p[0] for p in points) / len(points)
    avg_g = sum(p[1] for p in points) / len(points)
    avg_b = sum(p[2] for p in points) / len(points)
    avg_var = (max(avg_r, avg_g, avg_b) - min(avg_r, avg_g, avg_b))

    # === HYBRID DECISION ===
    # Terisi = sim RENDAH (tidak mirip template kosong)
    # Kosong = sim TINGGI (mirip template kosong)
    # Atau: sim di ambiguous zone + pixel warna homogen/gelap

    if max_sim >= 0.58:
        # Pasti kosong
        status = "KOSONG"
        is_empty = True
    elif max_sim < 0.40:
        # Pasti terisi
        status = "TERISI"
        is_empty = False
    else:
        # Ambiguous zone (0.40 - 0.58)
        # Cek pixel: kalau warna homogen (var rendah) → kosong
        # Kalau warna beragam (var tinggi) → terisi
        if avg_var < 30:
            status = "KOSONG*"
            is_empty = True
        else:
            status = "TERISI*"
            is_empty = False

    slots.append(not is_empty)

    print(f"   {i:<4} {slot_x:<6} {max_sim:<8.3f} {avg_var:<6.0f} "
          f"{avg_r:<5.0f} {avg_g:<5.0f} {avg_b:<5.0f} {status}")

terisi = sum(slots)
kosong = TOTAL_SLOTS - terisi
print(f"\n   📊 {terisi} terisi + {kosong} kosong = {TOTAL_SLOTS} total")

print(f"\n   POSISI TAP (slot terisi):")
for i, is_terisi in enumerate(slots):
    if is_terisi:
        tap_x = START_X + (i * GAP_X) + (tw // 2)
        print(f"   Slot {i}: tap ({tap_x}, {TAP_Y})")

print("\nSELESAI. Copy output ke sini!")