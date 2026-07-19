import cv2
import numpy as np
import os
import time
import random
import json
import ctypes
import subprocess
import tempfile
from ppadb.client import Client as AdbClient

# ╔══════════════════════════════════════════════════════════════╗
# ║              KONFIGURASI PROYEK & PATH                      ║
# ╚══════════════════════════════════════════════════════════════╝
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")
CONFIG_FILE = os.path.join(BASE_DIR, "account_config.json")

# ╔══════════════════════════════════════════════════════════════╗
# ║              DAFTAR AKUN (15 AKUN)                          ║
# ╠═══════╦═════════════════╦══════╦═════════════════════════════╣
# ║ Index ║ Nama            ║ TH   ║ Keterangan                 ║
# ╠═══════╬═════════════════╬══════╬═════════════════════════════╣
# ║   0   ║ Selimut         ║  11  ║ Akun second, ada DE        ║
# ║   1   ║ Ayam            ║   9  ║ Akun second, ada DE        ║
# ║   2   ║ MossyBoss       ║  ??  ║ Akun utama clan            ║
# ║   3   ║ MossyMinion 1   ║   5  ║ Tidak ada DE               ║
# ║   4   ║ MossyMinion 2   ║   5  ║ Tidak ada DE               ║
# ║   5   ║ MossyMinion 3   ║   4  ║ Tidak ada DE               ║
# ║   6   ║ MossyMinion 4   ║   4  ║ Tidak ada DE               ║
# ║   7   ║ MossyMinion 5   ║   4  ║ Tidak ada DE               ║
# ║   8   ║ MossyMinion 6   ║   4  ║ Tidak ada DE               ║
# ║   9   ║ MossyMinion 7   ║   4  ║ Tidak ada DE               ║
# ║  10   ║ MossyMinion 8   ║   4  ║ Tidak ada DE               ║
# ║  11   ║ MossyMinion 9   ║   4  ║ Tidak ada DE               ║
# ║  12   ║ MossyMinion 10  ║   4  ║ Tidak ada DE               ║
# ║  13   ║ MossyMinion 11  ║   4  ║ Tidak ada DE               ║
# ║  14   ║ MossyMinion 12  ║   4  ║ Tidak ada DE               ║
# ╚═══════╩═════════════════╩══════╩═════════════════════════════╝
DAFTAR_AKUN = [
    # (filename_scid, nama)
    ("scid_selimut.png",  "Selimut"),        # Index 0
    ("scid_ayam.png",     "Ayam"),           # Index 1
    ("scid_moss.png",     "MossyBoss"),      # Index 2
    ("scid_moss1.png",    "MossyMinion 1"),  # Index 3
    ("scid_moss2.png",    "MossyMinion 2"),  # Index 4
    ("scid_moss3.png",    "MossyMinion 3"),  # Index 5
    ("scid_moss4.png",    "MossyMinion 4"),  # Index 6
    ("scid_moss5.png",    "MossyMinion 5"),  # Index 7
    ("scid_moss6.png",    "MossyMinion 6"),  # Index 8
    ("scid_moss7.png",    "MossyMinion 7"),  # Index 9
    ("scid_moss8.png",    "MossyMinion 8"),  # Index 10
    ("scid_moss9.png",    "MossyMinion 9"),  # Index 11
    ("scid_moss10.png",   "MossyMinion 10"), # Index 12
    ("scid_moss11.png",   "MossyMinion 11"), # Index 13
    ("scid_moss12.png",   "MossyMinion 12"), # Index 14
]

# ╔══════════════════════════════════════════════════════════════╗
# ║              KONFIGURASI FARMING                             ║
# ╚══════════════════════════════════════════════════════════════╝
# Index akun mulai (lihat tabel di atas)
# Contoh: 7 = mulai dari MossyMinion 5
INDEX_AKUN_MULAI = 0

# Batas waktu aman per akun (kalau resource nggak penuh-penuh)
# 3600 = 1 Jam | 1800 = 30 Menit | 900 = 15 Menit
MAKSIMAL_WAKTU_PER_AKUN = 3600

# Paksa auto-detect DE ulang setiap kali? (True = ya, False = pakai cache)
FORCE_REDETECT_DE = False

# Tunggu macro zoom selesai (detik)
MACRO_WAIT = 6


# ╔══════════════════════════════════════════════════════════════╗
# ║              MANAJEMEN CONFIG FILE (DE DETECTION)           ║
# ╚══════════════════════════════════════════════════════════════╝
def load_config():
    """Load config dari file JSON. Buat baru kalau belum ada."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(config):
    """Simpan config ke file JSON."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_punya_de(scid_file, config):
    """Ambil status DE dari config. Return None kalau belum ada."""
    if scid_file in config:
        return config[scid_file].get("punya_de", None)
    return None


# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-DETECT DE STORAGE                          ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_de_availability():
    screencap = device.screencap()
    img = cv2.imdecode(
        np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
    )
    b, g, r = img[140, 910]
    punya_de = bool(r < 80 and g < 80 and b < 80)  # ← tambah bool()
    print(f"   🔍 DE [140,910]: R={r} G={g} B={b} "
          f"→ {'Ada DE' if punya_de else 'Tidak ada DE'}")
    return punya_de


# ╔══════════════════════════════════════════════════════════════╗
# ║              KONEKSI ADB                                     ║
# ╚══════════════════════════════════════════════════════════════╝
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi oleh ADB!")
    exit()
device = devices[0]
print(f"✅ Terhubung ke emulator: {device.serial}")


# ╔══════════════════════════════════════════════════════════════╗
# ║              ZOOM OUT: VBS APPACTIVATE + QUICK RETURN        ║
# ╚══════════════════════════════════════════════════════════════╝
import subprocess
import tempfile

class ZoomController:
    """Zoom out via VBS AppActivate + SendKeys (Shift+Z).

    1. VBS activate LDPlayer + kirim Shift+Z (trigger macro)
    2. Python re-attach thread + kembalikan window sebelumnya
    3. Tunggu macro selesai (4.5 detik)
    4. Scroll kamera ke view cerah
    """

    user32 = ctypes.windll.user32

    def __init__(self):
        self.hwnd_ld = None
        self._cari_ldplayer()

    def _cari_ldplayer(self):
        hasil = []
        ENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_int, ctypes.c_int
        )

        def callback(hwnd, _):
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if "ldplayer" in title.lower():
                    if self.user32.IsWindowVisible(hwnd):
                        hasil.append((hwnd, title))
            return True

        self.user32.EnumWindows(ENUMPROC(callback), 0)

        if hasil:
            self.hwnd_ld = hasil[0][0]
            print(f"✅ LDPlayer window: [{self.hwnd_ld}] {hasil[0][1]}")
        else:
            print("❌ LDPlayer window tidak ditemukan!")

    def _get_title(self, hwnd):
        length = self.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value
        return "Unknown"

    def zoom_out(self):
        """Zoom out: VBS → Shift+Z → quick return → scroll."""
        if not self.hwnd_ld:
            print("⚠️ LDPlayer window tidak ada, skip zoom")
            return False

        # === Simpan window aktif ===
        hwnd_prev = self.user32.GetForegroundWindow()
        title_prev = self._get_title(hwnd_prev)

        # === VBS: AppActivate + Shift+Z ===
        vbs_path = os.path.join(tempfile.gettempdir(), "zoom.vbs")
        with open(vbs_path, "w") as f:
            f.write('Set s = WScript.CreateObject("WScript.Shell")\n')
            f.write('s.AppActivate "LDPlayer"\n')
            f.write('WScript.Sleep 200\n')
            f.write('s.SendKeys "+z"')

        subprocess.run(
            ["cscript", "//nologo", vbs_path],
            capture_output=True, timeout=10
        )
        os.unlink(vbs_path)

        # === Tunggu macro register ===
        time.sleep(0.5)

        # === Kembalikan window (re-attach) ===
        hwnd_now = self.user32.GetForegroundWindow()
        tid_now = self.user32.GetWindowThreadProcessId(hwnd_now, None)
        tid_prev = self.user32.GetWindowThreadProcessId(hwnd_prev, None)

        self.user32.AttachThreadInput(tid_now, tid_prev, True)
        self.user32.BringWindowToTop(hwnd_prev)
        self.user32.SetForegroundWindow(hwnd_prev)
        self.user32.AttachThreadInput(tid_now, tid_prev, False)

        print(f"🔍 Zoom triggered! (kembali ke: {title_prev[:40]})")

        # === Tunggu macro selesai ===
        print(f"⏳ Macro ({MACRO_WAIT}s)...")
        time.sleep(MACRO_WAIT)

        # === Scroll ke view cerah ===
        print("📜 Scroll kamera ke view cerah...")
        device.shell("input swipe 480 400 480 100 400")
        time.sleep(1)
        device.shell("input swipe 480 400 480 100 400")
        time.sleep(1)

        print("✅ Zoom selesai!")
        return True


zoom_ctrl = ZoomController()


# ╔══════════════════════════════════════════════════════════════╗
# ║              FUNGSI UTILITAS                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def find_and_click(template_name, threshold=0.85, random_offset=True):
    img_path = os.path.join(GAMBAR_DIR, template_name)
    if not os.path.exists(img_path):
        return False

    template = cv2.imread(img_path, cv2.IMREAD_COLOR)
    screencap = device.screencap()
    screen_img = cv2.imdecode(
        np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
    )

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
        print(f"🎯 Tap {template_name} ({max_val:.2f})")
        return True
    return False

def clear_event_popups():
    """Bersihkan pop-up event (Continue/Skip) — handle satu kali atau looping."""
    cleared = 0
    for _ in range(20):  # Maks 20 kali (safety net)
        found = False

        if find_and_click("event_continue.png", threshold=0.85):
            print(f"   🎁 Event Continue! (ke-{cleared + 1})")
            time.sleep(2)
            found = True

        if not found and find_and_click("event_skip.png", threshold=0.85):
            print(f"   🎁 Event Skip! (ke-{cleared + 1})")
            time.sleep(2)
            found = True

        if found:
            cleared += 1
        else:
            break  # Tidak ada pop-up lagi

    if cleared > 0:
        print(f"   ✅ {cleared} pop-up event ditutup")
        
def clear_popups_and_recover():
    print("🧹 Membersihkan pop-up...")

    # Event pop-up dulu (paling sering muncul belakangan ini)
    clear_event_popups()

    # Pop-up umum
    if find_and_click("close_x.png", threshold=0.80):
        print("❌ Menutup pop-up!")
        time.sleep(1.5)

    for _ in range(2):
        device.shell("input tap 850 50")
        time.sleep(0.3)


def cek_status_resource(punya_de=True):
    """Cek kapasitas storage berdasarkan warna pixel."""
    print("🔍 Mengecek kapasitas Storage...")
    screencap = device.screencap()
    img = cv2.imdecode(
        np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
    )

    b_g, g_g, r_g = img[39, 760]
    b_e, g_e, r_e = img[91, 760]

    gold_full = (
        (180 <= r_g <= 255) and
        (160 <= g_g <= 255) and
        (0 <= b_g <= 150)
    )
    elixir_full = (
        (150 <= r_e <= 255) and
        (150 <= b_e <= 255) and
        (0 <= g_e <= 100)
    )

    if punya_de:
        b_d, g_d, r_d = img[140, 810]
        de_full = (
            (0 <= r_d <= 80) and
            (0 <= g_d <= 50) and
            (0 <= b_d <= 90)
        )
    else:
        de_full = False

    return gold_full, elixir_full, de_full


def is_storage_penuh(gold_full, elixir_full, de_full, punya_de=True):
    if punya_de:
        return gold_full and elixir_full and de_full
    else:
        return gold_full and elixir_full


def format_resource_status(gold_full, elixir_full, de_full, punya_de):
    """Format status resource untuk tampilan rapi."""
    de_str = 'FULL' if de_full else ('OK' if punya_de else 'N/A')
    return (
        f"   💰 Gold   : {'FULL' if gold_full else 'OK'}\n"
        f"   💎 Elixir : {'FULL' if elixir_full else 'OK'}\n"
        f"   ⚫ DE     : {de_str}"
    )


# ╔══════════════════════════════════════════════════════════════╗
# ║              FUNGSI PERTEMPURAN                              ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_brutal():
    """Deploy ngebut: 2 titik per kartu + instant ability."""
    print("⚔️ Brutal Deploy...")
    start_x = 180
    start_y = 495
    gap_x = 61
    total_slots = 10
    titik_lompat = [(350, 80), (600, 85)]

    for i in range(total_slots):
        slot_x = start_x + (i * gap_x)
        device.shell(f"input tap {slot_x} {start_y}")
        time.sleep(0.1)

        for base_x, base_y in titik_lompat:
            jx = base_x + random.randint(-15, 15)
            jy = base_y + random.randint(-10, 10)
            device.shell(f"input swipe {jx} {jy} {jx} {jy} 2200")

        time.sleep(0.3)
        device.shell(f"input tap {slot_x} {start_y}")
        time.sleep(0.1)

    spell_x = 480 + random.randint(-20, 20)
    spell_y = 300 + random.randint(-20, 20)
    device.shell(f"input tap {spell_x} {spell_y}")


def battle_sequence():
    """Eksekusi satu battle penuh."""
    clear_popups_and_recover()

    if find_and_click("attack_home.png"):
        time.sleep(1.5)
        if find_and_click("find_match.png"):
            time.sleep(2)
            print("⚙️ Konfirmasi Army...")
            if find_and_click("attack_setup.png"):
                print("⏳ Loading awan...")
                time.sleep(5)

                start_battle = time.time()
                deploy_brutal()

                target_duration = random.randint(100, 110)
                sisa = int(target_duration - (time.time() - start_battle))
                print(f"🔥 Deploy selesai! Cut-off: {sisa}s...")

                battle_ended = False
                while (time.time() - start_battle) < target_duration:
                    time.sleep(3)
                    if find_and_click("return_home.png", threshold=0.89):
                        print("🎉 Battle selesai!")
                        device.shell("input tap 476 459")
                        battle_ended = True
                        time.sleep(4)
                        break

                if not battle_ended:
                    print("⏱️ Cut-off! Force exit...")
                    device.shell("input tap 62 420")
                    time.sleep(1.5)
                    device.shell("input tap 584 344")
                    time.sleep(3)
                    device.shell("input tap 476 459")
                    time.sleep(4)
            else:
                print("❌ Attack Setup tidak ditemukan!")


# ╔══════════════════════════════════════════════════════════════╗
# ║              MANAJEMEN AKUN                                  ║
# ╚══════════════════════════════════════════════════════════════╝
def switch_next_account(target_scid_image):
    """Ganti ke akun target via settings."""
    print(f"🔄 Berganti ke: {target_scid_image}...")
    clear_popups_and_recover()

    if find_and_click("settings_gear.png"):
        time.sleep(1.5)
        if find_and_click("switch_account.png"):
            print("📋 Mencari akun target...")
            time.sleep(3)

            for _ in range(5):
                if find_and_click(target_scid_image, threshold=0.94):
                    print(f"✅ Akun ditemukan!")
                    time.sleep(10)
                    return True
                else:
                    print("⬇️ Scroll...")
                    device.shell("input swipe 480 400 480 150 600")
                    time.sleep(1.5)

            print(f"❌ Akun tidak ditemukan!")
            device.shell("input keyevent 4")
            return False
    return False


# ╔══════════════════════════════════════════════════════════════╗
# ║              MASTER LOOP                                     ║
# ╚══════════════════════════════════════════════════════════════╝
def main_farming_loop():
    """Farming loop utama: resource-based + auto-detect DE + macro zoom."""

    # ==========================================
    # HEADER
    # ==========================================
    print()
    print("🚀" + "=" * 53)
    print("   BOT FARMING v3 — AUTO DE + MACRO ZOOM")
    print("=" * 55)
    print(f"   📋 Total akun    : {len(DAFTAR_AKUN)}")
    print(f"   ▶️  Mulai dari    : Index {INDEX_AKUN_MULAI} "
          f"({DAFTAR_AKUN[INDEX_AKUN_MULAI][1]})")
    print(f"   🔍 Zoom method   : Brief Focus + Shift+X")
    print(f"   🤖 Auto-detect DE: {'Ya' if True else 'Tidak'}")
    print(f"   ⏱️ Safety net     : {MAKSIMAL_WAKTU_PER_AKUN // 60} menit/akun")
    print("=" * 55)

    # ==========================================
    # LOAD CONFIG (DE detection cache)
    # ==========================================
    config = load_config()

    # ==========================================
    # SWITCH KE AKUN AWAL
    # ==========================================
    scid_awal, nama_awal = DAFTAR_AKUN[INDEX_AKUN_MULAI]
    print(f"\n🔄 Switch ke akun awal: {nama_awal} (Index {INDEX_AKUN_MULAI})")

    if not switch_next_account(scid_awal):
        print(f"❌ Gagal switch ke {nama_awal}! Bot berhenti.")
        return

    print("⏳ Menunggu village loading...")
    time.sleep(8)

    # ==========================================
    # LOOP PER AKUN
    # ==========================================
    total_akun = len(DAFTAR_AKUN)
    total_battle_semua = 0
    start_total = time.time()

    for indeks in range(INDEX_AKUN_MULAI, total_akun):
        scid_file, nama = DAFTAR_AKUN[indeks]

        # ==========================================
        # HEADER PER AKUN
        # ==========================================
        print()
        print("┌" + "─" * 53 + "┐")
        print(f"│  AKUN : {nama.upper():<20} "
              f"[Index {indeks}, {indeks + 1}/{total_akun}]")
        print(f"│  SCID : {scid_file}")
        print("└" + "─" * 53 + "┘")

        # ==========================================
        # SWITCH AKUN (kecuali akun pertama di loop)
        # ==========================================
        if indeks > INDEX_AKUN_MULAI:
            if not switch_next_account(scid_file):
                print(f"⚠️ Gagal pindah ke {nama}, skip...")
                continue
            print("⏳ Menunggu village loading...")
            time.sleep(8)

        # ==========================================
        # ZOOM OUT (Brief Focus + Shift+X, sekali)
        # ==========================================
        zoom_ctrl.zoom_out()
        time.sleep(1)

        # ==========================================
        # AUTO-DETECT DE (atau baca dari cache)
        # ==========================================
        punya_de = get_punya_de(scid_file, config)

        if punya_de is not None and not FORCE_REDETECT_DE:
            print(f"   📋 DE dari cache: "
                  f"{'Ada' if punya_de else 'Tidak ada'}")
        else:
            print(f"   🤖 Auto-detect DE...")
            punya_de = detect_de_availability()
            config[scid_file] = {"punya_de": punya_de}
            save_config(config)
            print(f"   💾 Disimpan ke config")

        # ==========================================
        # CEK RESOURCE AWAL
        # ==========================================
        gold_full, elixir_full, de_full = cek_status_resource(punya_de)
        print(format_resource_status(
            gold_full, elixir_full, de_full, punya_de
        ))

        if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
            print(f"   ⚠️ Storage PENUH! Langsung skip.")
            continue

        # ==========================================
        # FARMING SAMPAI PENUH
        # ==========================================
        start_sesi = time.time()
        battle_count = 0

        while True:
            battle_sequence()
            battle_count += 1
            total_battle_semua += 1
            print(f"\n   ⚔️ Battle #{battle_count} [{nama}] selesai")

            time.sleep(2)
            clear_popups_and_recover()
            time.sleep(1)

            # Cek resource
            gold_full, elixir_full, de_full = cek_status_resource(punya_de)
            print(format_resource_status(
                gold_full, elixir_full, de_full, punya_de
            ))

            # Cek penuh
            if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                print(f"   ✅ Storage PENUH setelah {battle_count} battle!")
                break

            # Safety net
            elapsed = time.time() - start_sesi
            if elapsed > MAKSIMAL_WAKTU_PER_AKUN:
                print(f"   ⏱️ Safety net {MAKSIMAL_WAKTU_PER_AKUN // 60}m!")
                break

            menit = int(elapsed // 60)
            detik = int(elapsed % 60)
            sisa = MAKSIMAL_WAKTU_PER_AKUN - elapsed
            print(f"   ⏱️ Farming: {menit}m {detik}s | "
                  f"Sisa: {int(sisa // 60)}m {int(sisa % 60)}s")
            time.sleep(2)

        # Akun terakhir?
        if indeks >= total_akun - 1:
            break

    # ==========================================
    # RINGKASAN AKHIR
    # ==========================================
    total_waktu = time.time() - start_total
    menit_total = int(total_waktu // 60)
    detik_total = int(total_waktu % 60)

    print()
    print("=" * 55)
    print("   🎉 MISI SELESAI!")
    print("=" * 55)
    print(f"   📊 Total battle  : {total_battle_semua}")
    print(f"   📋 Total akun    : {len(DAFTAR_AKUN)}")
    print(f"   ⏱️ Total waktu   : {menit_total}m {detik_total}s")
    print(f"   🛑 Bot berhenti aman.")
    print("=" * 55)


if __name__ == "__main__":
    main_farming_loop()