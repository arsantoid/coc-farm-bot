import cv2
import numpy as np
from ppadb.client import Client as AdbClient

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi!")
    exit()

device = devices[0]

screencap = device.screencap()
img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

print("=" * 60)
print(f"   SCAN AREA DE BAR — Resolusi: {img.shape[1]}x{img.shape[0]}")
print("=" * 60)
print()
print("   Format: [Y, X] → R, G, B")
print()

# ==========================================
# SCAN LEBAR: Y=125 sampai Y=155, X=895 sampai X=945
# Tiap 5 pixel supaya tidak terlalu banyak
# ==========================================
print("-" * 60)
print("   SCAN GRID (tiap 5px)")
print("-" * 60)

print(f"   {'':6s}", end="")
for x in range(910, 940, 5):
    print(f"  X={x:3d}", end="")
print()
print("   " + "-" * 56)

for y in range(125, 160, 5):
    print(f"   Y={y:3d}", end="")
    for x in range(895, 950, 5):
        b, g, r = img[y, x]
        # Tampilkan singkat: R saja dulu supaya rapi
        print(f"  {r:3d},{g:3d},{b:3d}", end="")
    print()

print()

# ==========================================
# SCAN DETAIL: Titik-titik penting
# ==========================================
print("-" * 60)
print("   TITIK PENTING")
print("-" * 60)

titik_penting = [
    # Area DE bar (kalau ada)
    (135, 895, "DE bar kiri-atas"),
    (135, 910, "DE bar tengah-atas"),
    (135, 930, "DE bar kanan-atas"),
    (140, 895, "DE bar kiri"),
    (140, 910, "DE bar tengah"),
    (140, 930, "DE bar kanan"),
    (145, 895, "DE bar kiri-bawah"),
    (145, 910, "DE bar tengah-bawah"),
    (145, 930, "DE bar kanan-bawah"),
    (150, 910, "DE bar paling bawah"),
    # Area luar DE bar (background village)
    (120, 910, "Atas DE bar (bg)"),
    (160, 910, "Bawah DE bar (bg)"),
    (140, 870, "Kiri DE bar (bg)"),
    (140, 955, "Kanan DE bar (bg)"),
    # Pembanding: Gold & Elixir (selalu ada)
    (39,  760, "GOLD bar (pembanding)"),
    (91,  760, "ELIXIR bar (pembanding)"),
]

for y, x, label in titik_penting:
    b, g, r = img[y, x]
    gelap = "GELAP" if (r < 80 and g < 80 and b < 100) else "TERANG"
    print(f"   [{y:3d},{x:3d}] {label:28s} → R={r:3d} G={g:3d} B={b:3d}  [{gelap}]")

print()

# ==========================================
# SCAN LEBAR LAGI: Coba area X lebih ke kiri
# (mana tau DE bar posisinya bukan di 895-945)
# ==========================================
print("-" * 60)
print("   SCAN X LEBAR (Y=140, X=750 sampai X=960)")
print("-" * 60)

print(f"   Y=140: ", end="")
for x in range(750, 940, 10):
    b, g, r = img[140, x]
    gelap = "*" if (r < 80 and g < 80 and b < 100) else " "
    print(f"{r:3d},{g:3d},{b:3d}{gelap} ", end="")
    if (x - 750) % 80 == 70:
        print()
    print(f"         ", end="") if False else None
print()

print()
print("=" * 60)
print("   CATATAN:")
print("   * = pixel gelap (kemungkinan DE bar/icon)")
print("   Spasi = pixel terang (village background)")
print("=" * 60)