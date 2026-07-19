# ==========================================
# TEST_SLOT_V2.py
# Deteksi slot troop (11 slot, auto start_x)
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

tw, th = empty_template.shape[1], empty_template.shape[0]
THRESHOLD = 0.55

print(f"✅ Template: {tw}x{th}")
print(f"✅ Threshold: {THRESHOLD}")

screencap = device.screencap()
screen = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
print(f"✅ Screen: {screen.shape[1]}x{screen.shape[0]}")

# ==========================================
# STEP 1: Cari semua slot kosong
# ==========================================
result = cv2.matchTemplate(screen, empty_template, cv2.TM_CCOEFF_NORMED)

locations = np.where(result >= THRESHOLD)
matches = list(zip(locations[1], locations[0]))
matches.sort(key=lambda p: p[0])

# Group berdasarkan X
unique_empty = []
for x, y in matches:
    if not unique_empty or (x - unique_empty[-1][0]) > tw // 2:
        unique_empty.append((x, float(result[y, x])))

print(f"\n   Slot kosong terdeteksi: {len(unique_empty)}")
for i, (x, sim) in enumerate(unique_empty):
    print(f"   Kosong #{i}: X={x}, sim={sim:.3f}")

# ==========================================
# STEP 2: Hitung start_x dari pola
# ==========================================
if unique_empty:
    first_empty_x = unique_empty[0][0]

    # Hitung mundur: berapa slot terisi sebelum kosong pertama
    filled_before = 0
    test_x = first_empty_x - tw
    while test_x >= 0:
        x1 = max(0, test_x)
        x2 = min(result.shape[1], test_x + tw)
        area = result[:, x1:x2]
        max_sim = float(np.max(area))
        if max_sim < THRESHOLD:
            filled_before += 1
            test_x -= tw
        else:
            break

    start_x = first_empty_x - (filled_before * tw)

    # Hitung mundur lagi: cek apakah ada slot lagi di kiri
    # (untuk cek apakah TOTAL_SLOTS > 10)
    extra_filled = 0
    test_x = start_x - tw
    while test_x >= 0:
        x1 = max(0, test_x)
        x2 = min(result.shape[1], test_x + tw)
        area = result[:, x1:x2]
        max_sim = float(np.max(area))
        if max_sim < THRESHOLD:
            extra_filled += 1
            test_x -= tw
        else:
            break

    if extra_filled > 0:
        start_x = start_x - (extra_filled * tw)
        filled_before += extra_filled
else:
    start_x = 168
    filled_before = 10

# Hitung total slot
total_slots = filled_before + len(unique_empty)

print(f"\n   Start X       : {start_x}")
print(f"   Slot terisi   : {filled_before}")
print(f"   Slot kosong    : {len(unique_empty)}")
print(f"   TOTAL SLOT     : {total_slots}")
print(f"   Gap (tw)       : {tw}")

# ==========================================
# STEP 3: Verifikasi setiap slot
# ==========================================
print(f"\n   VERIFIKASI ({total_slots} slot):")
print(f"   {'Slot':<6} {'X':<6} {'sim':<8} {'Status'}")
print("   " + "-" * 35)

slots = []
for i in range(total_slots):
    slot_x = start_x + (i * tw)

    if slot_x < 0 or slot_x + tw > result.shape[1]:
        slots.append(False)
        print(f"   {i:<6} {slot_x:<6} {'OOB':<8} KOSONG (out of bounds)")
        continue

    area = result[:, slot_x:slot_x + tw]
    max_sim = float(np.max(area))

    if max_sim >= THRESHOLD:
        slots.append(False)
        status = "KOSONG"
    else:
        slots.append(True)
        status = "TERISI"

    print(f"   {i:<6} {slot_x:<6} {max_sim:<8.3f} {status}")

terisi = sum(slots)
kosong = total_slots - terisi

print(f"\n   📊 {terisi} terisi + {kosong} kosong = {total_slots} total")

# ==========================================
# STEP 4: Info deploy
# ==========================================
TAP_Y = 456 + (th // 2)
print(f"\n   DEPLOY INFO:")
print(f"   Start X  : {start_x}")
print(f"   Gap      : {tw}")
print(f"   Tap Y    : {TAP_Y} (456 + {th // 2})")
print(f"   Max slots: {total_slots}")

# Tampilkan posisi tap untuk setiap slot terisi
print(f"\n   POSISI TAP (slot terisi saja):")
for i, terisi in enumerate(slots):
    if terisi:
        tap_x = start_x + (i * tw) + (tw // 2)
        print(f"   Slot {i}: tap ({tap_x}, {TAP_Y})")

print("\nSELESAI. Copy output ke sini!")