import cv2
import numpy as np
import os
import time
import random
import pyautogui
import pygetwindow as gw
from ppadb.client import Client as AdbClient

# ==========================================
# KONFIGURASI PROYEK & PATH
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")

DAFTAR_AKUN = [
    "scid_selimut.png",
    "scid_ayam.png",
    "scid_moss.png",    
    "scid_moss1.png",
    "scid_moss2.png",
    "scid_moss3.png",
    "scid_moss4.png",
    "scid_moss5.png",
    "scid_moss6.png",
    "scid_moss7.png",
    "scid_moss8.png",
    "scid_moss9.png",
    "scid_moss10.png",
    "scid_moss11.png",
    "scid_moss12.png"
]

# Durasi farming per akun. 
# SET KE 60 UNTUK TESTING PERPINDAHAN. SET KE 1800 UNTUK REAL RUN (30 Menit).
DURASI_PER_AKUN = 60 

# ==========================================
# KONEKSI INFRASTRUKTUR ADB
# ==========================================
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi oleh ADB!")
    exit()
device = devices[0]
print(f"✅ Terhubung ke emulator: {device.serial}")

# ==========================================
# FUNGSI UTILITAS & KONTROL
# ==========================================
def find_and_click(template_name, threshold=0.85, random_offset=True):
    img_path = os.path.join(GAMBAR_DIR, template_name)
    if not os.path.exists(img_path): 
        return False

    template = cv2.imread(img_path, cv2.IMREAD_COLOR)
    screencap = device.screencap()
    screen_img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
    
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        h, w = template.shape[:-1]
        click_x = max_loc[0] + (w // 2)
        click_y = max_loc[1] + (h // 2)
        
        if random_offset:
            click_x += random.randint(-5, 5)
            click_y += random.randint(-5, 5)
            
        device.shell(f"input tap {click_x} {click_y}")
        print(f"🎯 Tap {template_name} (Akurasi: {max_val:.2f})")
        return True
    return False

def clear_popups_and_recover():
    print("🧹 Mengecek dan membersihkan layar dari menu nyasar...")
    if find_and_click("close_x.png", threshold=0.80):
        print("❌ Menutup menu/pop-up yang menghalangi!")
        time.sleep(1.5) 
    
    for _ in range(2):
        device.shell("input tap 850 50")
        time.sleep(0.3)

def fix_camera_and_zoom(window_name="LDPlayer"):
    print("🔍 Menyesuaikan Zoom Kamera...")
    try:
        windows = gw.getWindowsWithTitle(window_name)
        if windows:
            win = windows[0]
            if win.isMinimized: 
                win.restore()
            win.activate()
            time.sleep(0.5) 
            
            active_window = gw.getActiveWindow()
            if active_window and window_name in active_window.title:
                print("✅ Keamanan lolos! Mengeksekusi Zoom (Ctrl + F9)...")
                for _ in range(6):
                    pyautogui.hotkey('ctrl', 'f9') 
                    time.sleep(0.15)
            else:
                print("⚠️ LDPlayer terhalang! Membatalkan pencet tombol.")
            time.sleep(0.5) 
            
        print("🔒 Menarik kamera mentok ke batas ujung map...")
        for _ in range(2):
            device.shell("input swipe 480 270 800 500 400")
            time.sleep(0.5)
            
        print("✅ Layar sudah fixed, siap deploy!")
        return True
    except Exception as e:
        print(f"⚠️ Terjadi error pada sistem jendela: {e}")
        return False

# ==========================================
# LOGIKA AUTO UPGRADE (BETA)
# ==========================================
def auto_upgrade_sequence():
    """Mencoba upgrade bangunan dari daftar rekomendasi Builder sebelum ganti akun"""
    print("\n🛠️ Memulai sekuens Auto-Upgrade...")
    clear_popups_and_recover()
    
    # 1. Klik Icon Wajah Builder di tengah-atas layar
    if find_and_click("builder_icon.png"):
        time.sleep(1.5)
        
        # 2. Klik baris Rekomendasi Upgrade Pertama
        if find_and_click("suggested_upgrade_1.png"):
            print("🏗️ Menemukan rekomendasi upgrade, mencoba eksekusi...")
            time.sleep(2) # Tunggu kamera in-game geser ke bangunan
            
            # 3. Klik tombol Upgrade (Bisa Gold atau Elixir)
            if find_and_click("btn_upgrade_gold.png", threshold=0.80) or find_and_click("btn_upgrade_elixir.png", threshold=0.80):
                time.sleep(1.5)
                
                # 4. SAFETY CHECK: Jebakan Gems!
                if find_and_click("close_x.png", threshold=0.80):
                    print("❌ Duit kurang atau Builder penuh! Menutup penawaran Gems...")
                    time.sleep(1)
                else:
                    print("✅ Upgrade berhasil dieksekusi!")
                    
    # 5. Sapu bersih layar untuk memastikan tidak ada menu tertinggal
    clear_popups_and_recover()
        
# ==========================================
# FUNGSI PERTEMPURAN (THE BERSERKER MODE)
# ==========================================
def deploy_brutal():
    """Deploy Ngebut: 2 Titik Saja + Instant Ability"""
    print("⚔️ Memulai Brutal Deploy (Card -> Deploy 2 Titik -> Ability Instant)...")
    
    start_x = 180
    start_y = 495
    gap_x = 61
    total_slots = 10 
    
    # HANYA 2 TITIK: Kiri-Tengah dan Kanan-Tengah
    titik_lompat = [(350, 80), (600, 85)]
    
    for i in range(total_slots):
        slot_x = start_x + (i * gap_x)
        
        # 1. Pilih Kartu
        device.shell(f"input tap {slot_x} {start_y}")
        time.sleep(0.1) 
        
        # 2. Deploy di 2 titik (Total ~4.4 detik per kartu)
        for base_x, base_y in titik_lompat:
            jx = base_x + random.randint(-15, 15)
            jy = base_y + random.randint(-10, 10)
            device.shell(f"input swipe {jx} {jy} {jx} {jy} 2200")
            
        # 3. PENCET KARTU YANG SAMA SEKALI LAGI (Instant Ability)
        time.sleep(0.3)
        device.shell(f"input tap {slot_x} {start_y}")
        time.sleep(0.1)
            
    # 4. Blind Tap Spell (Tetap di akhir untuk keamanan)
    spell_x = 480 + random.randint(-20, 20)
    spell_y = 300 + random.randint(-20, 20)
    device.shell(f"input tap {spell_x} {spell_y}")

def battle_sequence():
    """Siklus Pertempuran dengan Timer yang Diperbaiki"""
    clear_popups_and_recover()
    
    if find_and_click("attack_home.png"):
        time.sleep(1.5)
        if find_and_click("find_match.png"):
            time.sleep(2)
            
            print("⚙️ Mengkonfirmasi Army Setup...")
            if find_and_click("attack_setup.png"):
                print("⏳ Menunggu loading awan...")
                time.sleep(5) 
                
                fix_camera_and_zoom() 
                
                # STOPWATCH DIMULAI DARI SINI (Sebelum pasukan turun)
                start_battle = time.time()
                
                # Proses deploy 10 kartu dengan 2 titik memakan waktu sekitar ~45 detik
                deploy_brutal() 
                
                # Total target waktu pertempuran 100 - 110 detik
                target_duration = random.randint(100, 110)
                sisa_waktu = int(target_duration - (time.time() - start_battle))
                print(f"🔥 Deploy selesai! Sisa waktu tunggu: ~{sisa_waktu} detik...")
                
                battle_ended = False
                
                while (time.time() - start_battle) < target_duration:
                    time.sleep(3) 
                    
                    # Threshold dinaikkan ke 0.92 agar rumput hijau aman
                    if find_and_click("return_home.png", threshold=0.92):
                        print("🎉 Battle selesai alami! Eksekusi Return Home...")
                        device.shell("input tap 476 459")
                        battle_ended = True
                        time.sleep(4)
                        break 
                
                # CUT-OFF PAKSA KARENA WAKTU HABIS
                if not battle_ended:
                    print(f"⏱️ Waktu {target_duration} detik habis! Force Exit / Surrender...")
                    device.shell("input tap 62 420")    # End Battle
                    time.sleep(1.5)
                    device.shell("input tap 584 344")   # Okay
                    time.sleep(3)
                    device.shell("input tap 476 459")   # Return Home
                    time.sleep(4)
            else:
                print("❌ Tombol Attack Setup tidak ditemukan!")
                
# ==========================================
# MANAJEMEN AKUN (ROTASI)
# ==========================================
def switch_next_account(target_scid_image):
    """Fungsi ganti akun via SCID dengan fitur Auto-Scroll"""
    print(f"🔄 Mencari dan berganti ke akun: {target_scid_image}...")
    clear_popups_and_recover()
    
    if find_and_click("settings_gear.png"):
        time.sleep(1.5)
        if find_and_click("switch_account.png"):
            print("📋 Daftar SCID terbuka. Mencari akun target...")
            time.sleep(3) 
            
            akun_ditemukan = False
            for _ in range(5):
                if find_and_click(target_scid_image, threshold=0.85):
                    print(f"✅ Akun {target_scid_image} ditemukan dan diklik!")
                    akun_ditemukan = True
                    time.sleep(10) 
                    break
                else:
                    print("⬇️ Akun belum terlihat, melakukan scroll ke bawah...")
                    device.shell("input swipe 480 400 480 150 600")
                    time.sleep(1.5) 
                    
            if not akun_ditemukan:
                print(f"❌ GAGAL! Akun {target_scid_image} tidak ditemukan.")
                device.shell("input keyevent 4")
                return False
                
            return True
    return False

# ==========================================
# MASTER LOOP: FARMING -> UPGRADE -> ROTASI
# ==========================================
def main_farming_loop():
    print("🚀 BOT FARM & AUTO-UPGRADE CLAN MOSS BERJALAN 🚀")
    
    indeks_akun_sekarang = 0
    total_akun = len(DAFTAR_AKUN)
    
    while True:
        akun_aktif = DAFTAR_AKUN[indeks_akun_sekarang]
        print("\n" + "="*40)
        print(f"Mulai sesi untuk: {akun_aktif.replace('.png', '').upper()}")
        print("="*40)
        
        start_time = time.time()
        
        # 1. FASE FARMING
        while (time.time() - start_time) < DURASI_PER_AKUN:
            battle_sequence()
            
            waktu_berjalan = time.time() - start_time
            time_left = max(0, DURASI_PER_AKUN - waktu_berjalan)
            print(f"⏱️ Sisa waktu {akun_aktif}: {int(time_left/60)} Menit {int(time_left%60)} Detik")
            time.sleep(2)
            
        print(f"\n🛑 FASE FARMING SELESAI ({DURASI_PER_AKUN} detik habis).")
        
        # 2. FASE UPGRADE (Belanjakan Loot)
        auto_upgrade_sequence()
        
        # 3. FASE GANTI AKUN
        print("\n🔄 Bersiap pindah akun...")
        indeks_akun_sekarang = (indeks_akun_sekarang + 1) % total_akun
        akun_target = DAFTAR_AKUN[indeks_akun_sekarang]
        
        berhasil = switch_next_account(akun_target)
        
        if not berhasil:
            print(f"⚠️ Gagal pindah ke {akun_target}! Memaksa lanjut loop berikutnya...")

if __name__ == "__main__":
    main_farming_loop()