# ==========================================
# ZOOM_BATCHED.py
# Semua event dikirim dalam 1 shell script
# Jalankan: python zoom_batched.py
# ==========================================

import time
import tempfile
import os
from ppadb.client import Client as AdbClient

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi!")
    exit()

device = devices[0]
print(f"✅ Terhubung: {device.serial}")

# ==========================================
# KONFIGURASI (dari hasil deteksi kamu)
# ==========================================
EVENT = "/dev/input/event2"
CX, CY = 480, 270      # Pusat layar 960x540
INITIAL = 40            # Jarak awal jari dari pusat
STEP = 25               # Jarak pergerakan per step
STEPS = 10              # Jumlah step zoom out


def generate_zoom_script():
    """Generate seluruh gesture sebagai 1 shell script.
    Semua event dijalankan berurutan TANPA jeda ADB."""

    dev = EVENT
    lines = ["#!/system/bin/sh"]

    # === TOUCH DOWN: Assign tracking ID ke 2 jari ===
    lines.append(f"sendevent {dev} 3 47 0")      # Slot 0
    lines.append(f"sendevent {dev} 3 57 100")     # Tracking ID jari 1
    lines.append(f"sendevent {dev} 3 47 1")       # Slot 1
    lines.append(f"sendevent {dev} 3 57 101")     # Tracking ID jari 2
    lines.append(f"sendevent {dev} 0 0 0")        # SYN

    # === POSISI AWAL: 2 jari dekat pusat ===
    f1x, f1y = CX - INITIAL, CY - INITIAL
    f2x, f2y = CX + INITIAL, CY + INITIAL

    lines.append(f"sendevent {dev} 3 47 0")
    lines.append(f"sendevent {dev} 3 53 {f1x}")   # X jari 1
    lines.append(f"sendevent {dev} 3 54 {f1y}")   # Y jari 1
    lines.append(f"sendevent {dev} 3 58 1")        # Pressure
    lines.append(f"sendevent {dev} 3 47 1")
    lines.append(f"sendevent {dev} 3 53 {f2x}")   # X jari 2
    lines.append(f"sendevent {dev} 3 54 {f2y}")   # Y jari 2
    lines.append(f"sendevent {dev} 3 58 1")
    lines.append(f"sendevent {dev} 0 0 0")
    lines.append("sleep 0.05")                      # Kecil saja

    # === GERAKKAN JARI KE LUAR (PINCH OUT) ===
    for step in range(1, STEPS + 1):
        offset = INITIAL + (step * STEP)

        f1x = max(5, CX - offset)
        f1y = max(5, CY - offset)
        f2x = min(955, CX + offset)
        f2y = min(535, CY + offset)

        lines.append(f"sendevent {dev} 3 47 0")
        lines.append(f"sendevent {dev} 3 53 {f1x}")
        lines.append(f"sendevent {dev} 3 54 {f1y}")
        lines.append(f"sendevent {dev} 3 58 1")
        lines.append(f"sendevent {dev} 3 47 1")
        lines.append(f"sendevent {dev} 3 53 {f2x}")
        lines.append(f"sendevent {dev} 3 54 {f2y}")
        lines.append(f"sendevent {dev} 3 58 1")
        lines.append(f"sendevent {dev} 0 0 0")
        lines.append("sleep 0.08")

    # === TOUCH UP: Lepas kedua jari ===
    lines.append(f"sendevent {dev} 3 47 0")
    lines.append(f"sendevent {dev} 3 57 -1")      # Release jari 1
    lines.append(f"sendevent {dev} 3 47 1")
    lines.append(f"sendevent {dev} 3 57 -1")      # Release jari 2
    lines.append(f"sendevent {dev} 0 0 0")

    return "\n".join(lines)


def jalankan_zoom():
    """Push script ke emulator, jalankan, lalu tarik kamera."""
    print("🔍 Membuat script zoom...")
    script = generate_zoom_script()

    # Simpan ke file lokal
    local_tmp = os.path.join(tempfile.gettempdir(), "zoom.sh")
    with open(local_tmp, "w") as f:
        f.write(script)

    # Push ke emulator
    remote_path = "/data/local/tmp/zoom.sh"
    device.push(local_tmp, remote_path)
    os.unlink(local_tmp)

    # Jalankan SEKALI (semua event sekaligus!)
    print("🚀 Menjalankan pinch-out gesture...")
    result = device.shell(f"sh {remote_path}")
    if result:
        print(f"   Output: {result}")

    time.sleep(1)

    # Tarik kamera ke ujung map
    print("🔒 Menarik kamera ke ujung map...")
    for _ in range(2):
        device.shell("input swipe 480 270 800 500 400")
        time.sleep(0.5)

    print("✅ Selesai!")


if __name__ == "__main__":
    print("=" * 50)
    print("   ZOOM-OUT (BATCHED SENDEVENT)")
    print("=" * 50)
    print(f"   Device: {EVENT}")
    print(f"   Steps: {STEPS}")
    print(f"   Step size: {STEP}px")
    print("=" * 50)
    print("\nTekan ENTER untuk jalankan...")
    input()
    jalankan_zoom()