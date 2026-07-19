import cv2
import numpy as np
import os
import time
import random
import json
import ctypes
import logging
import subprocess
import tempfile
from ppadb.client import Client as AdbClient

# ╔══════════════════════════════════════════════════════════════╗
# ║              KONFIGURASI PROYEK & PATH                      ║
# ╚══════════════════════════════════════════════════════════════╝
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")
CONFIG_FILE = os.path.join(BASE_DIR, "account_config.json")
DEBUG_DIR = os.path.join(BASE_DIR, "debug")

os.makedirs(DEBUG_DIR, exist_ok=True)

# ╔══════════════════════════════════════════════════════════════╗
# ║              LOGGING                                        ║
# ╚══════════════════════════════════════════════════════════════╝
logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'bot_log.txt'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════════════════╗
# ║              DAFTAR AKUN                                    ║
# ╚══════════════════════════════════════════════════════════════╝
DAFTAR_AKUN = [
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
# ║              KONFIGURASI                                     ║
# ╚══════════════════════════════════════════════════════════════╝
INDEX_AKUN_MULAI = 5
MAKSIMAL_WAKTU_PER_AKUN = 3600
FORCE_REDETECT_DE = False
MACRO_WAIT = 6

# ── SLOT DETECTION ──
EMPTY_SLOT_THRESHOLD = 0.50

# ── SPELL ──
SPELL_TEMPLATES = [
    "spell_rage.png",
    "spell_freeze.png",
    "spell_lightning.png",
]

# Area deploy spell (horizontal band di tengah base musuh)
SPELL_DEPLOY_TARGETS = [
    (280, 300),
    (370, 310),
    (450, 300),
    (530, 310),
    (610, 300),
]

# ── DEPLOY ──
SPELL_CHECK_INTERVAL = 3
LOOT_WAIT_MIN = 20
LOOT_WAIT_MAX = 30


# ╔══════════════════════════════════════════════════════════════╗
# ║              KONEKSI ADB                                     ║
# ╚══════════════════════════════════════════════════════════════╝
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi oleh ADB!")
    logger.error("Emulator tidak terdeteksi!")
    exit()
device = devices[0]
print(f"✅ Terhubung ke emulator: {device.serial}")
logger.info(f"Terhubung ke emulator: {device.serial}")


# ╔══════════════════════════════════════════════════════════════╗
# ║              CONFIG FILE                                     ║
# ╚══════════════════════════════════════════════════════════════╝
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_punya_de(scid_file, config):
    if scid_file in config:
        return config[scid_file].get("punya_de", None)
    return None


# ╔══════════════════════════════════════════════════════════════╗
# ║              DEBUG SCREENSHOT                                ║
# ╚══════════════════════════════════════════════════════════════╝
def save_debug_screenshot(label="error"):
    try:
        screencap = device.screencap()
        img = cv2.imdecode(
            np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
        )
        filename = f"{label}_{int(time.time())}.png"
        path = os.path.join(DEBUG_DIR, filename)
        cv2.imwrite(path, img)
        print(f"📸 Debug: {filename}")
        logger.info(f"Debug screenshot: {filename}")
    except Exception as e:
        print(f"⚠️ Gagal screenshot debug: {e}")


# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-DETECT DE                                  ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_de_availability():
    screencap = device.screencap()
    img = cv2.imdecode(
        np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
    )
    b, g, r = img[140, 910]
    punya_de = bool(r < 80 and g < 80 and b < 80)
    print(f"   🔍 DE [140,910]: R={r} G={g} B={b} "
          f"→ {'Ada DE' if punya_de else 'Tidak ada DE'}")
    logger.info(f"DE detection: R={r} G={g} B={b} → {punya_de}")
    return punya_de


# ╔══════════════════════════════════════════════════════════════╗
# ║              ZOOM CONTROLLER                                 ║
# ╚══════════════════════════════════════════════════════════════╝
class ZoomController:
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
        if not self.hwnd_ld:
            print("⚠️ LDPlayer window tidak ada, skip zoom")
            return False

        hwnd_prev = self.user32.GetForegroundWindow()
        title_prev = self._get_title(hwnd_prev)

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

        time.sleep(0.5)

        hwnd_now = self.user32.GetForegroundWindow()
        tid_now = self.user32.GetWindowThreadProcessId(hwnd_now, None)
        tid_prev = self.user32.GetWindowThreadProcessId(hwnd_prev, None)

        self.user32.AttachThreadInput(tid_now, tid_prev, True)
        self.user32.BringWindowToTop(hwnd_prev)
        self.user32.SetForegroundWindow(hwnd_prev)
        self.user32.AttachThreadInput(tid_now, tid_prev, False)

        print(f"🔍 Zoom triggered! (kembali ke: {title_prev[:40]})")
        print(f"⏳ Macro ({MACRO_WAIT}s)...")
        time.sleep(MACRO_WAIT)

        # Scroll DOWN = kamera ke ATAS (base musuh)
        print("📜 Scroll kamera ke atas (swipe down)...")
        device.shell("input swipe 480 100 480 400 400")
        time.sleep(1)
        device.shell("input swipe 480 100 480 400 400")
        time.sleep(1)

        print("✅ Zoom selesai!")
        return True


zoom_ctrl = ZoomController()


# ╔══════════════════════════════════════════════════════════════╗
# ║              TEMPLATE MATCHING (DASAR)                       ║
# ╚══════════════════════════════════════════════════════════════╝
def find_template(template_name, threshold=0.85):
    img_path = os.path.join(GAMBAR_DIR, template_name)
    if not os.path.exists(img_path):
        return None

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
        return (click_x, click_y, max_val)
    return None


def find_and_click(template_name, threshold=0.85, random_offset=True):
    pos = find_template(template_name, threshold)
    if pos:
        click_x, click_y, acc = pos
        if random_offset:
            click_x += random.randint(-5, 5)
            click_y += random.randint(-5, 5)
        device.shell(f"input tap {click_x} {click_y}")
        print(f"🎯 Tap {template_name} ({acc:.2f})")
        return True
    return False


# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-DETECT TROOP SLOTS (HYBRID)                ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_troop_slots():
    """Deteksi slot kosong vs terisi via hybrid detection.

    Hybrid: template matching + pixel color variance.
    Grid: start_x=168, gap=58, total=11, Y tap=495
    """
    empty_path = os.path.join(GAMBAR_DIR, "empty_slot.png")
    if not os.path.exists(empty_path):
        print("   ⚠️ empty_slot.png tidak ada! Assume semua terisi.")
        return [True] * 11

    empty_template = cv2.imread(empty_path, cv2.IMREAD_COLOR)
    screencap = device.screencap()
    screen = cv2.imdecode(
        np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
    )

    tw = empty_template.shape[1]  # 58
    START_X = 168
    TOTAL_SLOTS = 11
    TAP_Y = 495

    result = cv2.matchTemplate(
        screen, empty_template, cv2.TM_CCOEFF_NORMED
    )

    slots = []
    for i in range(TOTAL_SLOTS):
        slot_x = START_X + (i * tw)

        # CHECK 1: Template matching
        x1 = max(0, slot_x)
        x2 = min(result.shape[1], slot_x + tw)
        area = result[:, x1:x2]
        max_sim = float(np.max(area))

        # CHECK 2: Pixel color variance
        cx = slot_x + (tw // 2)
        cx = min(max(cx, 0), screen.shape[1] - 1)
        points = []
        for dy in [-10, 0, 10]:
            py = min(max(TAP_Y + dy, 0), screen.shape[0] - 1)
            b, g, r = screen[py, cx]
            points.append((int(r), int(g), int(b)))
        avg_r = sum(p[0] for p in points) / 3
        avg_g = sum(p[1] for p in points) / 3
        avg_b = sum(p[2] for p in points) / 3
        color_var = max(avg_r, avg_g, avg_b) - min(avg_r, avg_g, avg_b)

        # HYBRID DECISION
        if max_sim >= 0.58:
            is_filled = False
            status = "KOSONG"
        elif max_sim < 0.40:
            is_filled = True
            status = "TERISI"
        elif color_var >= 30:
            is_filled = True
            status = "TERISI*"
        else:
            is_filled = False
            status = "KOSONG*"

        slots.append(is_filled)
        print(f"   Slot {i}: {status} (sim={max_sim:.3f}, "
              f"var={color_var:.0f})")

    terisi = sum(slots)
    print(f"   📊 {terisi}/{TOTAL_SLOTS} slot terisi")
    return slots


# ╔══════════════════════════════════════════════════════════════╗
# ║              PIXEL CHECK HELPER                              ║
# ╚══════════════════════════════════════════════════════════════╝
def is_slot_filled_by_pixel(screen, slot_x, tw, tap_y=495):
    cx = slot_x + (tw // 2)
    cx = min(max(cx, 0), screen.shape[1] - 1)
    points = []
    for dy in [-10, 0, 10]:
        py = min(max(tap_y + dy, 0), screen.shape[0] - 1)
        b, g, r = screen[py, cx]
        points.append((int(r), int(g), int(b)))
    avg_r = sum(p[0] for p in points) / 3
    avg_g = sum(p[1] for p in points) / 3
    avg_b = sum(p[2] for p in points) / 3
    color_var = max(avg_r, avg_g, avg_b) - min(avg_r, avg_g, avg_b)
    return color_var >= 30


# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY SPELL (TEMPLATE ONLY, NO PIXEL FALLBACK) ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_spell_once():
    """Deploy spell SATU KALI via template matching only.

    Tidak pakai pixel fallback supaya tidak false positive
    (slot troop yang sudah kosong tapi pixel masih colorful).

    Return: jumlah spell yang di-deploy (0 atau 1)
    """
    if not SPELL_TEMPLATES:
        return 0

    for spell_file in SPELL_TEMPLATES:
        spell_path = os.path.join(GAMBAR_DIR, spell_file)
        if not os.path.exists(spell_path):
            continue

        template = cv2.imread(spell_path, cv2.IMREAD_COLOR)
        if template is None:
            continue

        h, w = template.shape[:2]

        screencap = device.screencap()
        screen_img = cv2.imdecode(
            np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR
        )

        bar_area = screen_img[456:540, 0:960]
        result = cv2.matchTemplate(
            bar_area, template, cv2.TM_CCOEFF_NORMED
        )
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.80:
            spell_x = max_loc[0] + (w // 2)
            spell_y = max_loc[1] + (h // 2) + 456

            device.shell(f"input tap {spell_x} {spell_y}")
            time.sleep(0.3)

            if SPELL_DEPLOY_TARGETS:
                target = random.choice(SPELL_DEPLOY_TARGETS)
                tx = target[0] + random.randint(-30, 30)
                ty = target[1] + random.randint(-20, 20)
                device.shell(f"input tap {tx} {ty}")
                print(f"   🔮 {spell_file} ({max_val:.2f}) "
                      f"→ ({tx},{ty})")
                time.sleep(0.5)

            return 1

    return 0


def deploy_all_remaining_spells():
    """Deploy semua spell sisa (loop template sampai habis)."""
    total = 0
    for _ in range(15):
        n = deploy_spell_once()
        if n == 0:
            break
        total += n

    if total > 0:
        print(f"   ✅ {total} spell sisa deployed!")
        logger.info(f"Spells sisa deployed: {total}")
    return total


# ╔══════════════════════════════════════════════════════════════╗
# ║              POPUP & RESOURCE                                ║
# ╚══════════════════════════════════════════════════════════════╝
def clear_event_popups():
    cleared = 0
    for _ in range(20):
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
            break

    if cleared > 0:
        print(f"   ✅ {cleared} pop-up event ditutup")
        logger.info(f"Event popups cleared: {cleared}")


def clear_popups_and_recover():
    print("🧹 Membersihkan pop-up...")
    clear_event_popups()

    if find_and_click("close_x.png", threshold=0.80):
        print("❌ Menutup pop-up!")
        time.sleep(1.5)

    for _ in range(2):
        device.shell("input tap 850 50")
        time.sleep(0.3)

def handle_connection_lost():
    """Cek dan handle layar Connection Lost.

    Return: True jika connection lost terdeteksi dan ditangani,
            False jika tidak ada connection lost.
    """
    if find_and_click("try_again.png", threshold=0.85):
        print("   🔌 Connection lost terdeteksi! Klik TRY AGAIN...")
        logger.info("Connection lost detected, clicking TRY AGAIN")
        time.sleep(5)

        # Cek lagi apakah masih connection lost
        if find_and_click("try_again.png", threshold=0.85):
            print("   🔌 Masih connection lost, coba lagi...")
            logger.info("Still connection lost, retrying")
            time.sleep(5)

            # Kalau masih gagal, coba return home
            if find_and_click("return_home.png", threshold=0.85):
                print("   🏠 Return HOME dari connection lost")
                logger.info("Connection lost: returning home")
                time.sleep(5)
                return True

        return True
    return False

def cek_status_resource(punya_de=True):
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
    de_str = 'FULL' if de_full else ('OK' if punya_de else 'N/A')
    return (
        f"   💰 Gold   : {'FULL' if gold_full else 'OK'}\n"
        f"   💎 Elixir : {'FULL' if elixir_full else 'OK'}\n"
        f"   ⚫ DE     : {de_str}"
    )


# ╔══════════════════════════════════════════════════════════════╗
# ║              CAMERA CONSISTENCY                              ║
# ╚══════════════════════════════════════════════════════════════╝
def normalize_camera():
    """Geser kamera ke ATAS (base musuh).

    Swipe DOWN = kamera ke ATAS = base musuh.
    """
    print("📷 Normalisasi kamera ke atas (swipe down)...")
    device.shell("input swipe 480 200 480 450 300")
    time.sleep(0.5)
    device.shell("input swipe 600 300 400 300 300")
    time.sleep(0.5)


# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY TROOP (INTERLEAVE, TANPA REDEPLOY)       ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_brutal():
    """Deploy: troop interleave spell, tanpa redeploy.

    Target: ~40 detik total → langsung surrender.
    Logika:
    1. Detect semua slot
    2. Deploy troop satu per satu
    3. Setiap 3 troop, cek & deploy spell via template
    4. Akhir: deploy sisa spell (template only)
    """
    print("⚔️ Memulai deploy...")

    normalize_camera()

    START_X = 168
    GAP_X = 58
    TAP_Y = 495
    titik_lompat = [(350, 80), (600, 85)]

    slots = detect_troop_slots()

    deployed_count = 0
    spell_count = 0

    # Interleave: troop → spell → troop → spell
    for i, terisi in enumerate(slots):
        if not terisi:
            continue

        slot_x = START_X + (i * GAP_X) + (GAP_X // 2)

        device.shell(f"input tap {slot_x} {TAP_Y}")
        time.sleep(0.1)

        for base_x, base_y in titik_lompat:
            jx = base_x + random.randint(-15, 15)
            jy = base_y + random.randint(-10, 10)
            device.shell(f"input swipe {jx} {jy} {jx} {jy} 2200")

        time.sleep(0.3)
        device.shell(f"input tap {slot_x} {TAP_Y}")
        time.sleep(0.1)
        deployed_count += 1

        print(f"   ✅ Troop slot {i} deployed "
              f"({deployed_count}/{sum(slots)})")

        # Cek spell setiap N troop
        if deployed_count % SPELL_CHECK_INTERVAL == 0:
            print(f"   🔮 Cek spell...")
            n = deploy_spell_once()
            spell_count += n

    # Akhir: sisa spell (template only)
    print(f"   🔮 Cek spell sisa...")
    spell_count += deploy_all_remaining_spells()

    print(f"   📊 Total: {deployed_count} troop + "
          f"{spell_count} spell")


# ╔══════════════════════════════════════════════════════════════╗
# ║              BATTLE SEQUENCE (FAST: DEPLOY → SURRENDER)      ║
# ╚══════════════════════════════════════════════════════════════╝
def battle_sequence():
    try:
        clear_popups_and_recover()

        # ── CEK CONNECTION LOST SEBELUM MULAI ──
        if handle_connection_lost():
            clear_popups_and_recover()
            time.sleep(2)

        if find_and_click("attack_home.png"):
            time.sleep(1.5)
            if find_and_click("find_match.png"):
                time.sleep(2)

                # ── CEK CONNECTION LOST SAAT CARI MATCH ──
                if handle_connection_lost():
                    print("   ⚠️ Connection lost saat cari match!")
                    return

                print("⚙️ Konfirmasi Army...")
                if find_and_click("attack_setup.png"):
                    print("⏳ Loading awan...")
                    time.sleep(5)

                    start_battle = time.time()
                    deploy_brutal()

                    deploy_time = int(time.time() - start_battle)
                    print(f"🔥 Deploy selesai! ({deploy_time}s)")

                    wait_time = random.randint(
                        LOOT_WAIT_MIN, LOOT_WAIT_MAX
                    )
                    print(f"⏳ Tunggu {wait_time}s untuk loot...")
                    time.sleep(wait_time)

                    # ── CEK CONNECTION LOST SEBELUM SURRENDER ──
                    if handle_connection_lost():
                        print("   ⚠️ Connection lost sebelum surrender!")
                        return

                    print("🏳️ Surrender!")
                    device.shell("input tap 62 420")
                    time.sleep(1.5)
                    device.shell("input tap 584 344")
                    time.sleep(3)
                    device.shell("input tap 476 459")
                    time.sleep(4)

                    # ── CEK CONNECTION LOST SETELAH SURRENDER ──
                    handle_connection_lost()

                    total_time = int(time.time() - start_battle)
                    print(f"✅ Battle selesai! ({total_time}s)")
                else:
                    print("❌ Attack Setup tidak ditemukan!")
                    save_debug_screenshot("no_attack_setup")
            else:
                print("❌ Find Match tidak ditemukan!")
                save_debug_screenshot("no_find_match")

                # ── MUNGKIN INI CONNECTION LOST ──
                if handle_connection_lost():
                    print("   ⚠️ Ternyata connection lost!")
        else:
            # ── INI YANG PALING PENTING ──
            # "no_attack_btn" kemungkinan besar connection lost
            if handle_connection_lost():
                print("   ⚠️ Ternyata connection lost!")
                logger.info("Connection lost handled at no_attack_btn")
            else:
                print("❌ Attack button tidak ditemukan!")
                save_debug_screenshot("no_attack_btn")

    except Exception as e:
        print(f"❌ ERROR di battle: {e}")
        logger.error(f"Battle error: {e}")
        save_debug_screenshot("battle_error")

        # ── CEK CONNECTION LOST SAAT ERROR ──
        if handle_connection_lost():
            print("   ⚠️ Connection lost saat error!")
            return

        print("🔧 Recovery...")
        for _ in range(3):
            device.shell("input keyevent 4")
            time.sleep(0.5)
        clear_popups_and_recover()
        time.sleep(2)


# ╔══════════════════════════════════════════════════════════════╗
# ║              MANAJEMEN AKUN                                  ║
# ╚══════════════════════════════════════════════════════════════╝
def switch_next_account(target_scid_image):
    print(f"🔄 Berganti ke: {target_scid_image}...")
    clear_popups_and_recover()

    try:
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
                        device.shell(
                            "input swipe 480 400 480 150 600"
                        )
                        time.sleep(1.5)

                print(f"❌ Akun tidak ditemukan!")
                device.shell("input keyevent 4")
                return False
    except Exception as e:
        print(f"❌ ERROR switch akun: {e}")
        logger.error(f"Switch error: {e}")
        save_debug_screenshot("switch_error")
        for _ in range(3):
            device.shell("input keyevent 4")
            time.sleep(0.5)

    return False


# ╔══════════════════════════════════════════════════════════════╗
# ║              MASTER LOOP                                     ║
# ╚══════════════════════════════════════════════════════════════╝
def main_farming_loop():
    print()
    print("🚀" + "=" * 53)
    print("   BOT FARMING v7 — FAST SURRENDER")
    print("=" * 55)
    print(f"   📋 Total akun    : {len(DAFTAR_AKUN)}")
    print(f"   ▶️  Mulai dari    : Index {INDEX_AKUN_MULAI} "
          f"({DAFTAR_AKUN[INDEX_AKUN_MULAI][1]})")
    print(f"   🔍 Zoom method   : VBS AppActivate + Shift+Z")
    print(f"   🤖 Auto-detect DE: Ya")
    print(f"   🃏 Slot detection: Hybrid (template + pixel)")
    print(f"   🔮 Spell deploy  : Template only (no pixel fallback)")
    print(f"   ⚔️ Battle mode    : Deploy → "
          f"{LOOT_WAIT_MIN}-{LOOT_WAIT_MAX}s → Surrender")
    print(f"   ⏱️ Safety net     : "
          f"{MAKSIMAL_WAKTU_PER_AKUN // 60} menit/akun")
    print("=" * 55)
    logger.info("Bot v7 started")

    config = load_config()

    scid_awal, nama_awal = DAFTAR_AKUN[INDEX_AKUN_MULAI]
    print(f"\n🔄 Switch ke akun awal: {nama_awal} "
          f"(Index {INDEX_AKUN_MULAI})")

    if not switch_next_account(scid_awal):
        print(f"❌ Gagal switch ke {nama_awal}! Bot berhenti.")
        logger.error(f"Gagal switch ke {nama_awal}")
        return

    print("⏳ Menunggu village loading...")
    time.sleep(8)

    total_akun = len(DAFTAR_AKUN)
    total_battle_semua = 0
    start_total = time.time()

    for indeks in range(INDEX_AKUN_MULAI, total_akun):
        scid_file, nama = DAFTAR_AKUN[indeks]

        print()
        print("┌" + "─" * 53 + "┐")
        print(f"│  AKUN : {nama.upper():<20} "
              f"[Index {indeks}, {indeks + 1}/{total_akun}]")
        print(f"│  SCID : {scid_file}")
        print("└" + "─" * 53 + "┘")
        logger.info(f"=== AKUN: {nama} ({indeks}/{total_akun}) ===")

        if indeks > INDEX_AKUN_MULAI:
            if not switch_next_account(scid_file):
                print(f"⚠️ Gagal pindah ke {nama}, skip...")
                logger.warning(f"Gagal pindah ke {nama}")
                continue
            print("⏳ Menunggu village loading...")
            time.sleep(8)

        zoom_ctrl.zoom_out()
        time.sleep(1)

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

        gold_full, elixir_full, de_full = cek_status_resource(punya_de)
        print(format_resource_status(
            gold_full, elixir_full, de_full, punya_de
        ))

        if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
            print(f"   ⚠️ Storage PENUH! Langsung skip.")
            logger.info(f"{nama}: Storage penuh, skip")
            continue

        start_sesi = time.time()
        battle_count = 0

        while True:
            battle_sequence()
            battle_count += 1
            total_battle_semua += 1
            print(f"\n   ⚔️ Battle #{battle_count} [{nama}] selesai")
            logger.info(f"Battle #{battle_count} [{nama}] selesai")


            time.sleep(2)
            handle_connection_lost()
            clear_popups_and_recover()
            time.sleep(1)

            gold_full, elixir_full, de_full = cek_status_resource(punya_de)
            print(format_resource_status(
                gold_full, elixir_full, de_full, punya_de
            ))

            if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                print(f"   ✅ Storage PENUH setelah "
                      f"{battle_count} battle!")
                logger.info(
                    f"{nama}: Storage penuh setelah "
                    f"{battle_count} battle"
                )
                break

            elapsed = time.time() - start_sesi
            if elapsed > MAKSIMAL_WAKTU_PER_AKUN:
                print(f"   ⏱️ Safety net "
                      f"{MAKSIMAL_WAKTU_PER_AKUN // 60}m!")
                logger.info(f"{nama}: Safety net tercapai")
                break

            menit = int(elapsed // 60)
            detik = int(elapsed % 60)
            sisa = MAKSIMAL_WAKTU_PER_AKUN - elapsed
            print(f"   ⏱️ Farming: {menit}m {detik}s | "
                  f"Sisa: {int(sisa // 60)}m {int(sisa % 60)}s")
            time.sleep(2)

        if indeks >= total_akun - 1:
            break

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
    logger.info(f"Bot selesai: {total_battle_semua} battle, "
                f"{menit_total}m {detik_total}s")


if __name__ == "__main__":
    main_farming_loop()