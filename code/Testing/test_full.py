import cv2
import numpy as np
from ppadb.client import Client as AdbClient

# ==========================================
# KONFIGURASI KOORDINAT
# ==========================================
X_GOLD = 760
Y_GOLD = 30

X_ELIXIR = 760
Y_ELIXIR = 80

X_DE = 810
Y_DE = 130

def test_cek_resource():
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    
    if len(devices) == 0:
        print("❌ Emulator tidak terdeteksi!")
        return
        
    device = devices[0]
    print("✅ Terhubung ke emulator. Mengambil screenshot...\n")
    
    screencap = device.screencap()
    img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
    
    # Ekstraksi BGR (Ingat: OpenCV pakainya B-G-R, bukan R-G-B)
    b_g, g_g, r_g = img[Y_GOLD, X_GOLD]
    b_e, g_e, r_e = img[Y_ELIXIR, X_ELIXIR]
    b_d, g_d, r_d = img[Y_DE, X_DE]
    
    print("="*40)
    print("🔎 HASIL ANALISIS PIKSEL RESOURCE 🔎")
    print("="*40)
    
    # ------------------------------------------
    # 1. CEK GOLD (KUNING)
    # ------------------------------------------
    print(f"\n🟡 GOLD @ ({X_GOLD}, {Y_GOLD}) --> B:{b_g} | G:{g_g} | R:{r_g}")
    if (180 <= r_g <= 255) and (160 <= g_g <= 255) and (0 <= b_g <= 150):
        print("   ✅ STATUS: GOLD FULL!")
    else:
        print("   ⏳ STATUS: Gold Belum Penuh")

    # ------------------------------------------
    # 2. CEK ELIXIR (UNGU)
    # ------------------------------------------
    # Elixir: Merah tinggi, Biru tinggi, Hijau rendah
    print(f"\n🟣 ELIXIR @ ({X_ELIXIR}, {Y_ELIXIR}) --> B:{b_e} | G:{g_e} | R:{r_e}")
    if (150 <= r_e <= 255) and (150 <= b_e <= 255) and (0 <= g_e <= 100):
        print("   ✅ STATUS: ELIXIR FULL!")
    else:
        print("   ⏳ STATUS: Elixir Belum Penuh")

    # ------------------------------------------
    # 3. CEK DARK ELIXIR (HITAM/GELAP)
    # ------------------------------------------
    # DE cukup tricky karena warnanya mirip background kapsul yang kosong.
    # Kita tes pakai threshold sangat gelap dulu.
    print(f"\n⚫ DARK ELIXIR @ ({X_DE}, {Y_DE}) --> B:{b_d} | G:{g_d} | R:{r_d}")
    if (0 <= r_d <= 80) and (0 <= g_d <= 50) and (0 <= b_d <= 90):
        print("   ✅ STATUS: DARK ELIXIR FULL!")
    else:
        print("   ⏳ STATUS: DE Belum Penuh / Tidak Ada")
        
    print("\n" + "="*40)

if __name__ == "__main__":
    test_cek_resource()