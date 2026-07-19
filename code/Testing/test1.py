import cv2
import numpy as np
import os
import time
from ppadb.client import Client as AdbClient

# 1. Setup Path Dinamis (menyesuaikan struktur foldermu)
# Ini akan melacak otomatis: dari folder 'code' mundur satu langkah, lalu masuk ke folder 'Gambar'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")

# 2. Koneksi ke ADB LDPlayer
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ LDPlayer tidak terdeteksi oleh ADB! Pastikan emulator menyala dan ADB diaktifkan.")
    exit()

device = devices[0]
print(f"✅ Berhasil terhubung ke emulator: {device.serial}")

def find_and_click(template_name, threshold=0.8):
    """Fungsi untuk mencari gambar di layar dan mengkliknya"""
    # Mengambil jalur absolut dari gambar yang mau dicari
    img_path = os.path.join(GAMBAR_DIR, template_name)
    
    # Cek apakah file gambar fisik benar-benar ada
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan di: {img_path}")
        return False

    # Load gambar template
    template = cv2.imread(img_path, cv2.IMREAD_COLOR)

    # Ambil screenshot langsung dari memory emulator
    screencap = device.screencap()
    screen_img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
    
    # Lakukan pencocokan gambar
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        # Hitung titik tengah gambar untuk diklik
        h, w = template.shape[:-1]
        click_x = max_loc[0] + (w // 2)
        click_y = max_loc[1] + (h // 2)
        
        print(f"🎯 Ditemukan '{template_name}' dengan akurasi {max_val:.2f}! Mengklik di koordinat X:{click_x} Y:{click_y}")
        
        # Kirim perintah klik via ADB
        device.shell(f"input tap {click_x} {click_y}")
        return True
    else:
        print(f"🔍 '{template_name}' tidak ada di layar (Akurasi terbaik cuma {max_val:.2f}).")
        return False

# --- BAGIAN TESTING ---
print("Membaca layar dalam 3 detik...")
time.sleep(3)

# Coba cari dan klik tombol attack di Home Village
find_and_click("attack_home.png")