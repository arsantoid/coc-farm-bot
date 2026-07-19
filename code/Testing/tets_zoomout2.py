# ==========================================
# ZOOM_OUT_FINAL.py
# Script zoom-out berdasarkan deteksi emulator kamu
# Jalankan: python zoom_out_final.py
# ==========================================

import time
from ppadb.client import Client as AdbClient

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi!")
    exit()

device = devices[0]
print(f"✅ Terhubung: {device.serial}")

# ==========================================
# KONFIGURASI DARI HASIL DETEKSI
# ==========================================
EVENT = "/dev/input/event2"  # Touchscreen device (dari getevent -pl)

# Koordinat touchscreen SAMA dengan layar (0-959, 0-539)
# Tidak perlu konversi

# Pusat layar
CX = 480
CY = 270

# Jarak awal jari dari pusat (saat pertama menyentuh)
INITIAL_OFFSET = 40

# Seberapa jauh jari bergerak ke luar per step
STEP_SIZE = 35

# Jumlah step (semakin banyak = semakin jauh zoom out)
ZOOM_STEPS = 12

# Delay antar step (detik). Semakin kecil = semakin cepat
STEP_DELAY = 0.2


def send(cmd):
    """Kirim satu sendevent command."""
    device.shell(f"sendevent {EVENT} {cmd}")


def commit():
    """Commit frame (SYN_REPORT)."""
    send("0 0 0")


def frame(f1_x, f1_y, f2_x, f2_y, pressure=1):
    """Kirim satu frame multitouch: dua jari sekaligus.

    Urutan pengiriman:
    1. Pilih slot 0 → set posisi jari 1 → set tekanan
    2. Pilih slot 1 → set posisi jari 2 → set tekanan
    3. Commit (SYN_REPORT) → Android membaca ini sebagai 1 gesture
    """
    # --- Jari 1 (slot 0) ---
    send(f"3 47 0")           # ABS_MT_SLOT = 0
    send(f"3 53 {f1_x}")      # ABS_MT_POSITION_X
    send(f"3 54 {f1_y}")      # ABS_MT_POSITION_Y
    send(f"3 58 {pressure}")  # ABS_MT_PRESSURE

    # --- Jari 2 (slot 1) ---
    send(f"3 47 1")           # ABS_MT_SLOT = 1
    send(f"3 53 {f2_x}")      # ABS_MT_POSITION_X
    send(f"3 54 {f2_y}")      # ABS_MT_POSITION_Y
    send(f"3 58 {pressure}")  # ABS_MT_PRESSURE

    # --- Commit ---
    commit()


def touch_down():
    """Sentuh layar dengan 2 jari dekat pusat."""
    # Jari 1: sedikit kiri-atas dari pusat
    # Jari 2: sedikit kanan-bawah dari pusat
    f1_x = CX - INITIAL_OFFSET
    f1_y = CY - INITIAL_OFFSET
    f2_x = CX + INITIAL_OFFSET
    f2_y = CY + INITIAL_OFFSET

    # Assign tracking ID per jari (wajib untuk multitouch)
    send("3 47 0")         # Slot 0
    send("3 57 100")       # Tracking ID 100

    send("3 47 1")         # Slot 1
    send("3 57 101")       # Tracking ID 101

    commit()

    # Kirim posisi awal
    frame(f1_x, f1_y, f2_x, f2_y)


def touch_up():
    """Angkat kedua jari."""
    send("3 47 0")         # Slot 0
    send("3 57 -1")        # Release tracking ID

    send("3 47 1")         # Slot 1
    send("3 57 -1")        # Release tracking ID

    commit()


def zoom_out():
    """Eksekusi zoom out (pinch-out gesture)."""
    print("🔍 Memulai zoom out via sendevent...")

    # 1. Sentuh dengan 2 jari dekat pusat
    touch_down()
    time.sleep(0.2)

    # 2. Gerakkan kedua jari ke arah luar (pinch out)
    for step in range(1, ZOOM_STEPS + 1):
        offset = INITIAL_OFFSET + (step * STEP_SIZE)

        f1_x = CX - offset      # Jari 1 makin ke kiri
        f1_y = CY - offset      # Jari 1 makin ke atas
        f2_x = CX + offset      # Jari 2 makin ke kanan
        f2_y = CY + offset      # Jari 2 makin ke bawah

        # Clamp supaya tidak keluar layar
        f1_x = max(10, f1_x)
        f1_y = max(10, f1_y)
        f2_x = min(950, f2_x)
        f2_y = min(530, f2_y)

        frame(f1_x, f1_y, f2_x, f2_y)
        print(f"   Step {step}/{ZOOM_STEPS}: "
              f"Jari1=({f1_x},{f1_y}) Jari2=({f2_x},{f2_y})")
        time.sleep(STEP_DELAY)

    # 3. Angkat jari
    touch_up()
    print("✅ Pinch-out gesture selesai!")

    # 4. Tarik kamera ke ujung map
    print("🔒 Menarik kamera ke ujung map...")
    time.sleep(0.5)
    for _ in range(2):
        device.shell("input swipe 480 270 800 500 400")
        time.sleep(0.5)

    print("✅ Zoom out selesai!")


# ==========================================
# MENU
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("   ZOOM-OUT SCRIPT (BERDASARKAN DETEKSI)")
    print("=" * 50)
    print(f"   Device: {EVENT}")
    print(f"   Resolusi: 960x540")
    print(f"   Zoom steps: {ZOOM_STEPS}")
    print("=" * 50)
    print()
    print("Tekan ENTER untuk jalankan zoom out...")
    input()
    zoom_out()
    print()
    print("💡 Jika zoom berhasil, script ini bisa di-import")
    print("   ke script utama farming.")