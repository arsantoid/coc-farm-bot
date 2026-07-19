import pyautogui
import pygetwindow as gw
import time
from ppadb.client import Client as AdbClient

# 1. KONEKSI ADB (Untuk melakukan swipe di dalam game)
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi oleh ADB!")
    exit()
device = devices[0]

def fix_camera_position(window_name="LDPlayer"):
    # 2. BAWA JENDELA KE DEPAN
    windows = gw.getWindowsWithTitle(window_name)
    if not windows:
        print(f"❌ Jendela '{window_name}' tidak ditemukan.")
        return False
        
    win = windows[0]
    if win.isMinimized:
        win.restore()
    win.activate()
    time.sleep(0.5) 
    
    # 3. ZOOM OUT EKSTREM (Spam F5 6 kali biar benar-benar mentok)
    print("🔍 Eksekusi Max Zoom Out...")
    for _ in range(6):
        pyautogui.press('f5')
        time.sleep(0.1) # Jeda super singkat antar pencetan
        
    time.sleep(0.5) # Tunggu animasi zoom selesai

    # 4. BOUNDARY LOCK (Kunci posisi kamera)
    # Menarik layar dari tengah (480, 270) ke arah kanan bawah (800, 500)
    # Ini akan membuat kamera in-game terdorong mentok ke sudut Kiri Atas
    print("🔒 Menstabilkan layar ke sudut batas map...")
    
    # Lakukan 2x swipe biar pasti mentok nabrak batas
    for _ in range(2):
        # Format: swipe X_awal Y_awal X_akhir Y_akhir durasi_ms
        device.shell("input swipe 480 270 800 500 400")
        time.sleep(0.5)

    print("✅ Layar sudah fixed dan siap untuk brutal deploy!")
    return True

# --- TESTING ---
print("Siap-siap! Buka base musuh di CoC, lalu minimize/pindah ke VS Code.")
print("Dalam 3 detik, bot akan Zoom Out Ekstrem dan Mengunci Layar!")
time.sleep(3)
fix_camera_position()