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
    ("scid_selimut.png",   "Selimut"),        # Index 0
    ("scid_ayam.png",      "Ayam"),           # Index 1
    ("scid_moss.png",      "MossyBoss"),      # Index 2
    ("scid_moss1.png",     "MossyMinion 1"),  # Index 3
    ("scid_moss2.png",     "MossyMinion 2"),  # Index 4
    ("scid_moss3.png",     "MossyMinion 3"),  # Index 5
    ("scid_moss4.png",     "MossyMinion 4"),  # Index 6
    ("scid_moss5.png",     "MossyMinion 5"),  # Index 7
    ("scid_moss6.png",     "MossyMinion 6"),  # Index 8
    ("scid_moss7.png",     "MossyMinion 7"),  # Index 9
    ("scid_moss8.png",     "MossyMinion 8"),  # Index 10
    ("scid_moss9.png",     "MossyMinion 9"),  # Index 11
    ("scid_moss10.png",    "MossyMinion 10"), # Index 12
    ("scid_moss11.png",    "MossyMinion 11"), # Index 13
    ("scid_moss12.png",    "MossyMinion 12"), # Index 14
]

# ╔══════════════════════════════════════════════════════════════╗
# ║              KONFIGURASI GLOBAL                             ║
# ╚══════════════════════════════════════════════════════════════╝
INDEX_AKUN_MULAI = 8
STOP_AFTER_INDEX = -1
LOOP_CONTINUOUSLY = False
MAKSIMAL_WAKTU_PER_AKUN = 3600
FORCE_REDETECT_DE = False
MACRO_WAIT = 6

# ── SPELL DEPLOYMENT (NORMAL) ──
SPELL_COORDS_1 = [              # 1 housing space: horizontal sebar
    (220, 320), (340, 330), (440, 320), (540, 330), (660, 320),
]

SPELL_COORDS_2 = [              # 2 housing space: segitiga kecil
    (440, 310), (340, 330), (540, 330),
]


# ── EVENT TROOP DEPLOYMENT ──
EVENT_TROOP_DEFS = [
    # "event_troop_clone.png",
    # Tambah sesuai event aktif, contoh: "event_troop_super.png"
]

EVENT_TROOP_COORDS =[]

EVENT_TROOP_SWIPE_DURATION = 3500

# ── EVENT SPELL DEPLOYMENT ──
EVENT_SPELL_DEFS = [
    # "event_spell_clone.png",
    # Tambah sesuai event aktif, contoh: "event_spell_rage.png"
]
EVENT_SPELL_COORDS = [
    # Ketupat filled rapat (25 titik)
    (420, 200),
    (370, 225), (470, 225),
    (320, 250), (420, 250), (520, 250),
    (270, 275), (370, 275), (470, 275), (570, 275),
    (220, 300), (320, 300), (420, 300), (520, 300), (620, 300),
    (270, 325), (370, 325), (470, 325), (570, 325),
    (320, 350), (420, 350), (520, 350),
    (370, 375), (470, 375),
    (420, 400),
]
EVENT_SPELL_MAX_TAPS = 40

# ── DEPLOY ──
LOOT_WAIT_MIN = 20
LOOT_WAIT_MAX = 30

# ── CONNECTION LOST ──
LOADING_TIMEOUT = 10
MATCH_FIND_TIMEOUT = 5

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-UPGRADE CONFIG                            ║
# ╚══════════════════════════════════════════════════════════════╝
ENABLE_UPGRADE_BUILDING = False
ENABLE_UPGRADE_LAB = False
UPGRADE_MODE = 1               # 1 atau 2
# Mode 1: Storage penuh → Upgrade → Next akun
#         Storage belum → Farm → Upgrade → Next akun
# Mode 2: Storage penuh → Upgrade → Farm lagi → Next akun
#         Storage belum → Farm → Upgrade → Farm lagi → Next akun

BUILDER_HEAD_X = 450
BUILDER_HEAD_Y = 25
LAB_ICON_X = 330
LAB_ICON_Y = 25
ITEM_OFFSET_Y = 28

CONFIRM_THRESHOLD  = 0.80
HEADER_THRESHOLD   = 0.80
UPGRADE_THRESHOLD  = 0.80
BUSY_THRESHOLD     = 0.90

CLOSE_X = 900
CLOSE_Y = 40

DELAY_AFTER_TAP   = 1.5
DELAY_AFTER_CLOSE = 1.0
DELAY_MENU_LOAD   = 3.0

TEMPLATE_HEADER    = "suggested_upgrades_text.png"
TEMPLATE_UPGRADE   = "upgrade_btn_dim.png"
TEMPLATE_CONFIRM   = "confirm_text.png"
TEMPLATE_BUSY      = "all_builders_busy.png"
TEMPLATE_LAB_BUSY  = "lab_busy.png"

# ╔══════════════════════════════════════════════════════════════╗
# ║              KONEKSI ADB                                    ║
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
# ║              CONFIG FILE                                    ║
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
# ║              DEBUG SCREENSHOT                               ║
# ╚══════════════════════════════════════════════════════════════╝
def save_debug_screenshot(label="error"):
    try:
        screencap = device.screencap()
        img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
        filename = f"{label}_{int(time.time())}.png"
        path = os.path.join(DEBUG_DIR, filename)
        cv2.imwrite(path, img)
        print(f"📸 Debug: {filename}")
        logger.info(f"Debug screenshot: {filename}")
    except Exception as e:
        print(f"⚠️ Gagal screenshot debug: {e}")

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-DETECT DE                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_de_availability():
    screencap = device.screencap()
    img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
    b, g, r = img[140, 910]
    punya_de = bool(r < 80 and g < 80 and b < 80)
    print(f"   🔍 DE [140,910]: R={r} G={g} B={b} → {'Ada DE' if punya_de else 'Tidak ada DE'}")
    logger.info(f"DE detection: R={r} G={g} B={b} → {punya_de}")
    return punya_de

# ╔══════════════════════════════════════════════════════════════╗
# ║              ZOOM CONTROLLER                                ║
# ╚══════════════════════════════════════════════════════════════╝
class ZoomController:
    user32 = ctypes.windll.user32

    def __init__(self):
        self.hwnd_ld = None
        self._cari_ldplayer()

    def _cari_ldplayer(self):
        hasil = []
        ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

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

        subprocess.run(["cscript", "//nologo", vbs_path], capture_output=True, timeout=10)
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

        print("📜 Scroll kamera ke atas (swipe down)...")
        device.shell("input swipe 480 100 480 400 400")
        time.sleep(1)
        device.shell("input swipe 480 100 480 400 400")
        time.sleep(1)

        print("✅ Zoom selesai!")
        return True

zoom_ctrl = ZoomController()

# ╔══════════════════════════════════════════════════════════════╗
# ║              TEMPLATE MATCHING (DASAR)                      ║
# ╚══════════════════════════════════════════════════════════════╝
def find_template(template_name, threshold=0.85):
    img_path = os.path.join(GAMBAR_DIR, template_name)
    if not os.path.exists(img_path):
        return None
    template = cv2.imread(img_path, cv2.IMREAD_COLOR)
    screencap = device.screencap()
    screen_img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

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
# ║              AUTO-DETECT TROOP SLOTS (HYBRID)               ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_troop_slots():
    empty_path = os.path.join(GAMBAR_DIR, "empty_slot.png")
    if not os.path.exists(empty_path):
        print("   ⚠️ empty_slot.png tidak ada! Assume semua terisi.")
        return [True] * 11

    empty_template = cv2.imread(empty_path, cv2.IMREAD_COLOR)
    screencap = device.screencap()
    screen = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

    tw = empty_template.shape[1]
    START_X = 168
    TOTAL_SLOTS = 11
    TAP_Y = 495

    result = cv2.matchTemplate(screen, empty_template, cv2.TM_CCOEFF_NORMED)
    slots = []

    for i in range(TOTAL_SLOTS):
        slot_x = START_X + (i * tw)
        x1 = max(0, slot_x)
        x2 = min(result.shape[1], slot_x + tw)
        area = result[:, x1:x2]
        max_sim = float(np.max(area))

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
        print(f"   Slot {i}: {status} (sim={max_sim:.3f}, var={color_var:.0f})")

    terisi = sum(slots)
    print(f"   📊 {terisi}/{TOTAL_SLOTS} slot terisi")
    return slots

# ╔══════════════════════════════════════════════════════════════╗
# ║              LOAD SAVED ARMY                                ║
# ╚══════════════════════════════════════════════════════════════╝
SAVED_RECIPE_X = 475
SAVED_RECIPE_Y = 50
USE_ARMY_X = 880
USE_ARMY_Y = 135

def load_saved_army():
    """Load saved army preset. Klik Saved Recipes → Use Army."""
    print("   🏋️ Loading saved army preset...")
    time.sleep(1)

    # Klik Saved Recipes tab
    device.shell(f"input tap {SAVED_RECIPE_X} {SAVED_RECIPE_Y}")
    time.sleep(1.5)

    # Klik Use Army
    device.shell(f"input tap {USE_ARMY_X} {USE_ARMY_Y}")
    time.sleep(2)

    print("   ✅ Saved army loaded!")

# ╔══════════════════════════════════════════════════════════════╗
# ║              DETEKSI BAR (TROOP/SPELL)                      ║
# ╚══════════════════════════════════════════════════════════════╝
def find_in_bar(template_file):
    """Cari troop/spell di bar bawah. Return (x, y, conf) atau None."""
    img_path = os.path.join(GAMBAR_DIR, template_file)
    if not os.path.exists(img_path):
        return None
    template = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if template is None:
        return None

    h, w = template.shape[:2]
    screencap = device.screencap()
    screen_img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
    bar_area = screen_img[456:540, 0:960]
    result = cv2.matchTemplate(bar_area, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= 0.96:
        click_x = max_loc[0] + (w // 2)
        click_y = max_loc[1] + (h // 2) + 456
        return (click_x, click_y, max_val)
    return None

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY SPELL (NORMAL)                          ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_spells_by_slots(spell_slot_indices):
    """Deploy spells berdasarkan slot terdeteksi. Ganjil → COORDS_1 (5 tap), Genap → COORDS_2 (3 tap)."""
    if not spell_slot_indices:
        return 0

    if not SPELL_COORDS_1 or not SPELL_COORDS_2:
        print("   ⚠️ Koordinat spell kosong!")
        return 0

    START_X = 168
    GAP_X = 58
    TAP_Y = 495

    total = 0
    for idx, si in enumerate(spell_slot_indices):
        slot_x = START_X + (si * GAP_X) + (GAP_X // 2)

        # Select spell di slot ini
        device.shell(f"input tap {slot_x} {TAP_Y}")
        time.sleep(0.2)

        # Pilih koordinat berdasarkan urutan: ganjil → COORDS_1, genap → COORDS_2
        if idx % 2 == 0:
            coords = SPELL_COORDS_1
            tipe = "COORDS_1"
        else:
            coords = SPELL_COORDS_2
            tipe = "COORDS_2"

        # Deploy di koordinat map
        taps = 0
        for cx, cy in coords:
            tx = cx + random.randint(-15, 15)
            ty = cy + random.randint(-15, 15)
            device.shell(f"input tap {tx} {ty}")
            taps += 1
            total += 1
            time.sleep(0.2)

        print(f"   🔮 Spell slot {si} ({idx + 1}/{len(spell_slot_indices)}) → {taps}x tap [{tipe}]")

    if total > 0:
        print(f"   ✅ {total} spell taps dari {len(spell_slot_indices)} slot!")
        logger.info(f"Spells: {total} taps dari {len(spell_slot_indices)} slot")
    return total

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY EVENT TROOPS                            ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_event_troops():
    """Deploy event troops di ujung map dengan swipe lebih lama."""
    if not EVENT_TROOP_DEFS:
        return 0

    total = 0

    for troop_file in EVENT_TROOP_DEFS:
        troop_pos = find_in_bar(troop_file)
        if not troop_pos:
            continue

        # Select event troop
        tx, ty, conf = troop_pos
        device.shell(f"input tap {tx} {ty}")
        time.sleep(0.3)

        # Deploy di semua koordinat pinggir
        for bx, by in EVENT_TROOP_COORDS:
            jx = bx + random.randint(-15, 15)
            jy = by + random.randint(-10, 10)
            device.shell(f"input swipe {jx} {jy} {jx} {jy} {EVENT_TROOP_SWIPE_DURATION}")
            total += 1
            time.sleep(0.2)

        print(f"   🎪 Event troop {troop_file} ({conf:.2f}) → {len(EVENT_TROOP_COORDS)}x swipe")

    if total > 0:
        print(f"   ✅ {total} event troop deployments!")
        logger.info(f"Event troops deployed: {total}")
    return total

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY EVENT SPELLS                            ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_event_spells():
    """Deploy event spells bentuk ketupat. Max 40 tap per ronde."""
    if not EVENT_SPELL_DEFS:
        return 0

    total_taps = 0

    for spell_file in EVENT_SPELL_DEFS:
        if total_taps >= EVENT_SPELL_MAX_TAPS:
            break

        spell_pos = find_in_bar(spell_file)
        if not spell_pos:
            continue

        sx, sy, conf = spell_pos
        device.shell(f"input tap {sx} {sy}")
        time.sleep(0.3)

        batch = 0
        while total_taps < EVENT_SPELL_MAX_TAPS:
            batch += 1
            taps_this = 0
            for cx, cy in EVENT_SPELL_COORDS:
                if total_taps >= EVENT_SPELL_MAX_TAPS:
                    break
                tx = cx + random.randint(-20, 20)
                ty = cy + random.randint(-20, 20)
                device.shell(f"input tap {tx} {ty}")
                total_taps += 1
                taps_this += 1
                time.sleep(0.15)

            print(f"   🎪 {spell_file} ({conf:.2f}) batch{batch} → {taps_this}x (total={total_taps})")

    if total_taps > 0:
        print(f"   ✅ {total_taps} event spell taps deployed!")
        logger.info(f"Event spells deployed: {total_taps}")
    return total_taps

# ╔══════════════════════════════════════════════════════════════╗
# ║              POPUP & RESOURCE                               ║
# ╚══════════════════════════════════════════════════════════════╝
def clear_event_popups():
    cleared = 0
    for _ in range(20):
        found = False

        if find_and_click("claim_reward_event.png", threshold=0.80):
            print(f"   🎁 Claim Reward! (ke-{cleared + 1})")
            time.sleep(2)
            for _ in range(4):
                device.shell(f"input tap {random.randint(920,930)} {random.randint(56,57)}")
                time.sleep(0.5)
            if find_and_click("event_continue.png", threshold=0.85):
                print(f"   🎁 Event Continue! (ke-{cleared + 1})")
                time.sleep(2)
            cleared += 1
            found = True

        if not found and find_and_click("event_continue.png", threshold=0.85):
            print(f"   🎁 Event Continue! (ke-{cleared + 1})")
            time.sleep(2)
            cleared += 1
            found = True

        if not found and find_and_click("event_skip.png", threshold=0.85):
            print(f"   🎁 Event Skip! (ke-{cleared + 1})")
            time.sleep(2)
            cleared += 1
            found = True

        if not found:
            break

    for _ in range(4):
        device.shell(f"input tap {random.randint(920,930)} {random.randint(56,57)}")
        time.sleep(0.5)

    if cleared > 0:
        print(f"   ✅ {cleared} pop-up event ditutup")
        logger.info(f"Event popups cleared: {cleared}")


def clear_popups_and_recover():
    print("🧹 Membersihkan pop-up...")

    clear_event_popups()

    for i in range(4):
        if find_and_click("okay_surrender.png", threshold=0.75):
            print(f"    Okay clicked ({i+1}/4)")
            time.sleep(0.8)
        else:
            break

    for i in range(4):
        if find_and_click("close_x.png", threshold=0.75):
            print(f"   ❌ Close X clicked ({i+1}/4)")
            time.sleep(0.8)
        else:
            break

    for i in range(4):
        device.shell(f"input tap {random.randint(920,930)} {random.randint(56,57)}")
        time.sleep(0.5)

    print("   ✅ Popup cleanup selesai")

# ╔══════════════════════════════════════════════════════════════╗
# ║              CONNECTION LOST HANDLER                        ║
# ╚══════════════════════════════════════════════════════════════╝
def handle_connection_lost():
    # ── RELOAD: akun tabrakan / stuck ──
    if find_and_click("reload.png", threshold=0.85):
        print("   🔄 RELOAD terdeteksi! Klik RELOAD...")
        logger.info("RELOAD detected, clicking RELOAD")
        time.sleep(8)
        return True

    if find_and_click("try_again.png", threshold=0.85):
        print("   🔌 Connection lost terdeteksi! Klik TRY AGAIN...")
        logger.info("Connection lost detected, clicking TRY AGAIN")
        time.sleep(5)

        if find_and_click("try_again.png", threshold=0.85):
            print("   🔌 Masih connection lost, coba lagi...")
            logger.info("Still connection lost, retrying")
            time.sleep(5)

            if find_and_click("return_home.png", threshold=0.85):
                print("   🏠 Return HOME dari connection lost")
                logger.info("Connection lost: returning home")
                time.sleep(5)
                return True
        return True
    return False


def close_ldplayer():
    """Minimize atau close LDPlayer setelah selesai sesi."""
    if zoom_ctrl.hwnd_ld:
        zoom_ctrl.user32.ShowWindow(zoom_ctrl.hwnd_ld, 6)  # SW_MINIMIZE
        print("   🖥️ LDPlayer minimized!")
        logger.info("LDPlayer minimized")
    else:
        print("   ⚠️ LDPlayer window tidak ditemukan, skip minimize")

def press_home():
    """Tekan tombol Home di emulator biar ga stuck di village."""
    device.shell("input keyevent 3")  # KEYCODE_HOME
    time.sleep(1)
    print("   🏠 Home button ditekan!")
    logger.info("Home button pressed")

def cek_status_resource(punya_de=True):
    print("🔍 Mengecek kapasitas Storage...")
    screencap = device.screencap()
    img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
    b_g, g_g, r_g = img[39, 760]
    b_e, g_e, r_e = img[91, 760]

    gold_full = ((180 <= r_g <= 255) and (160 <= g_g <= 255) and (0 <= b_g <= 150))
    elixir_full = ((150 <= r_e <= 255) and (150 <= b_e <= 255) and (0 <= g_e <= 100))

    if punya_de:
        b_d, g_d, r_d = img[140, 810]
        de_full = ((0 <= r_d <= 80) and (0 <= g_d <= 50) and (0 <= b_d <= 90))
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
# ║              CAMERA CONSISTENCY                             ║
# ╚══════════════════════════════════════════════════════════════╝
def normalize_camera():
    print("📷 Normalisasi kamera ke atas (swipe down)...")
    device.shell("input swipe 480 200 480 450 300")
    time.sleep(0.5)
    device.shell("input swipe 600 300 400 300 300")
    time.sleep(0.5)
    
# ╔══════════════════════════════════════════════════════════════╗
# ║              DETECT HERO & SIEGE SLOTS                      ║
# ╚══════════════════════════════════════════════════════════════╝
HERO_DEFS = [
    # (template_file, ability_delay_seconds)
    ("hero_king.png",      10),
    ("hero_queen.png",     2),
    ("hero_warden.png",    8),
    ("hero_minion.png",    12),
    # Slot 5 & 6 — isi nanti kalau udah SS
    # ("hero_x.png",       ?),
    # ("hero_y.png",       ?),
]

SIEGE_DEFS = [
    # "siege_wall_wrecker.png",
    # "siege_battle_blimp.png",
    # "siege_log_launcher.png",
    # "siege_flame_flinger.png",
]

def _find_slot_index(bar_x):
    """Konversi posisi X di bar → slot index (0-10)."""
    START_X = 168
    SLOT_W = 58
    idx = int((bar_x - START_X) / SLOT_W)
    return max(0, min(idx, 10))


def detect_special_slots():
    """Scan bar untuk deteksi posisi hero & siege."""
    hero_indices = {}    # {slot_index: delay}
    siege_indices = []

    for hero_file, ability_delay in HERO_DEFS:
        pos = find_in_bar(hero_file)
        if pos:
            hx, hy, conf = pos
            idx = _find_slot_index(hx)
            hero_indices[idx] = ability_delay
            print(f"   🦸 {hero_file} → slot {idx} delay={ability_delay}s ({conf:.2f})")

    for siege_file in SIEGE_DEFS:
        pos = find_in_bar(siege_file)
        if pos:
            sx, sy, conf = pos
            idx = _find_slot_index(sx)
            siege_indices.append(idx)
            print(f"   🚗 {siege_file} → slot {idx} ({conf:.2f})")

    return hero_indices, siege_indices

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY TROOP                                   ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_brutal():
    print("⚔️ Memulai deploy...")
    normalize_camera()

    START_X = 168
    GAP_X = 58
    TAP_Y = 495
    titik_lompat = [(350, 80), (600, 85)]

    # ── STEP 1: DETECT ──
    slots = detect_troop_slots()
    total_terisi = sum(slots)
    hero_slots, siege_slots = detect_special_slots()

    # Hitung boundary: hero/siege terakhir → setelahnya = spell
    if hero_slots:
        boundary = max(hero_slots.keys())
    elif siege_slots:
        boundary = max(siege_slots)
    else:
        filled = [i for i, t in enumerate(slots) if t]
        boundary = max(filled) if filled else -1

    # Spell = slot terisi SETELAH boundary
    spell_slot_indices = [i for i in range(boundary + 1, 11) if slots[i]]
    # Troop = semua slot terisi KECUALI spell
    troop_indices = [i for i, t in enumerate(slots) if t and i not in spell_slot_indices]

    print(f"   📊 {total_terisi} slot | Hero: {list(hero_slots.keys())} | Siege: {siege_slots} | Spell: {spell_slot_indices}")
    print(f"   📐 Boundary: slot {boundary} → {len(spell_slot_indices)} spell slot terdeteksi")

    # ── STEP 2: EVENT TROOPS ──
    event_troop_count = deploy_event_troops()

    # ── STEP 3: DEPLOY TROOP + SIEGE + HERO (SKIP spell slots) ──
    deployed_count = 0
    hero_deploy_info = []

    for i in troop_indices:
        slot_x = START_X + (i * GAP_X) + (GAP_X // 2)
        device.shell(f"input tap {slot_x} {TAP_Y}")
        time.sleep(0.1)

        # ── HERO: tap map, catat delay ──
        if i in hero_slots:
            for base_x, base_y in titik_lompat:
                hx = base_x + random.randint(-15, 15)
                hy = base_y + random.randint(-10, 10)
                device.shell(f"input tap {hx} {hy}")
                time.sleep(0.3)
            hero_deploy_info.append((slot_x, hero_slots[i]))
            print(f"   🦸 Hero slot {i} deployed! (delay={hero_slots[i]}s)")

        # ── SIEGE: 1 tap tengah ──
        elif i in siege_slots:
            sx = 480 + random.randint(-50, 50)
            sy = 270 + random.randint(-50, 50)
            device.shell(f"input tap {sx} {sy}")
            print(f"   🚗 Siege slot {i} deployed!")
            time.sleep(0.3)

        # ── TROOP: swipe ──
        else:
            for base_x, base_y in titik_lompat:
                jx = base_x + random.randint(-15, 15)
                jy = base_y + random.randint(-10, 10)
                device.shell(f"input swipe {jx} {jy} {jx} {jy} 2200")
            time.sleep(0.3)

        deployed_count += 1
        print(f"   ✅ Slot {i} ({deployed_count}/{len(troop_indices)})")

    # ── STEP 4: DELAY + SPELLS (slot-based) + HERO ABILITY ──
    if hero_deploy_info:
        max_delay = max(delay for _, delay in hero_deploy_info)
        print(f"   🦸 {len(hero_deploy_info)} hero. Max delay: {max_delay}s")

        start_wait = time.time()

        event_spell_count = deploy_event_spells()
        normal_spell_count = deploy_spells_by_slots(spell_slot_indices)

        spell_time = time.time() - start_wait
        remaining = max_delay - spell_time

        if remaining > 0:
            print(f"   ⏳ Sisa delay {remaining:.1f}s...")
            time.sleep(remaining)

        for slot_x, delay in hero_deploy_info:
            device.shell(f"input tap {slot_x} {TAP_Y}")
            print(f"   ⚡ Hero ability! (x={slot_x})")
            time.sleep(0.3)

    else:
        print(f"   🔮 Deploy spells...")
        event_spell_count = deploy_event_spells()
        normal_spell_count = deploy_spells_by_slots(spell_slot_indices)

    print(f"   📊 Total: {deployed_count} troop | {event_troop_count} event troop | {event_spell_count} event spell | {normal_spell_count} spell")

# ╔══════════════════════════════════════════════════════════════╗
# ║              BATTLE SEQUENCE                                ║
# ╚══════════════════════════════════════════════════════════════╝
def battle_sequence(army_loaded=False):
    """army_loaded = True kalau sudah load preset di akun ini."""
    try:
        clear_popups_and_recover()
        if handle_connection_lost():
            clear_popups_and_recover()
            time.sleep(2)

        if find_and_click("attack_home.png"):
            time.sleep(1.5)
            if find_and_click("find_match.png"):
                time.sleep(2)

                if handle_connection_lost():
                    print("   ⚠️ Connection lost saat cari match!")
                    logger.info("Connection lost during find match")
                    return army_loaded

                # ── LOAD SAVED ARMY (setelah find match, sekali per akun) ──
                if not army_loaded:
                    load_saved_army()
                    army_loaded = True

                print("⏳ Menunggu Attack Setup muncul...")
                found_setup = False
                for detik in range(1, MATCH_FIND_TIMEOUT + 1):
                    time.sleep(1)
                    if handle_connection_lost():
                        print("   ⚠️ Connection lost saat loading!")
                        logger.info("Connection lost during match load")
                        return army_loaded
                    if find_template("attack_setup.png"):
                        found_setup = True
                        print(f"   ✅ Attack Setup muncul (detik ke-{detik})")
                        break

                if not found_setup:
                    print(f"❌ Attack Setup tidak muncul setelah {MATCH_FIND_TIMEOUT}s!")
                    save_debug_screenshot("timeout_attack_setup")
                    return army_loaded

                print("⚙️ Konfirmasi Army...")
                find_and_click("attack_setup.png")

                print("⏳ Loading awan...")
                for detik in range(1, LOADING_TIMEOUT + 1):
                    time.sleep(1)
                    if handle_connection_lost():
                        print("   ⚠️ Connection lost saat loading awan!")
                        logger.info("Connection lost during cloud loading")
                        return army_loaded

                start_battle = time.time()
                deploy_brutal()

                deploy_time = int(time.time() - start_battle)
                print(f"🔥 Deploy selesai! ({deploy_time}s)")

                wait_time = random.randint(LOOT_WAIT_MIN, LOOT_WAIT_MAX)
                print(f"⏳ Tunggu {wait_time}s untuk loot...")

                for sisa in range(wait_time, 0, -1):
                    time.sleep(1)
                    if sisa % 5 == 0:
                        if handle_connection_lost():
                            print("   ⚠️ Connection lost saat loot!")
                            logger.info("Connection lost during loot wait")
                            return army_loaded

                if handle_connection_lost():
                    print("   ⚠️ Connection lost sebelum surrender!")
                    logger.info("Connection lost before surrender")
                    return army_loaded

                print("🏳️ Surrender!")
                device.shell("input tap 62 420")
                time.sleep(1.5)

                if handle_connection_lost():
                    print("   ⚠️ Connection lost saat surrender!")
                    logger.info("Connection lost during surrender")
                    return army_loaded

                device.shell("input tap 584 344")
                time.sleep(3)
                device.shell("input tap 476 459")
                time.sleep(4)

                handle_connection_lost()

                total_time = int(time.time() - start_battle)
                print(f"✅ Battle selesai! ({total_time}s)")
            else:
                if handle_connection_lost():
                    print("   ⚠️ Ternyata connection lost!")
                    logger.info("Connection lost at find_match failure")
                else:
                    print("❌ Find Match tidak ditemukan!")
                    save_debug_screenshot("no_find_match")
        else:
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

        if handle_connection_lost():
            print("   ⚠️ Connection lost saat error!")
            logger.info("Connection lost handled during error")
            return army_loaded

        print("🔧 Recovery...")
        for _ in range(3):
            device.shell("input keyevent 4")
            time.sleep(0.5)
        clear_popups_and_recover()
        time.sleep(2)

    return army_loaded

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-UPGRADE BUILDING                          ║
# ╚══════════════════════════════════════════════════════════════╝
def auto_upgrade_building():
    """Upgrade building + hero via Builder Head menu."""
    print("\n🏠 ════════════════════════════════════════")
    print("   AUTO-UPGRADE: BUILDING + HERO")
    print("   ════════════════════════════════════════")

    upgraded = 0
    skipped = 0
    busy_hit = 0

    # Klik Builder Head setiap kali masuk
    print(f"   [1] Klik Builder Head ({BUILDER_HEAD_X}, {BUILDER_HEAD_Y})...")
    device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
    time.sleep(DELAY_MENU_LOAD)

    while True:
        # Cek connection lost
        if handle_connection_lost():
            print("   ⚠️ Connection lost saat upgrade building!")
            clear_popups_and_recover()
            return upgraded

        # Scan header
        header = find_template(TEMPLATE_HEADER, HEADER_THRESHOLD)
        if not header:
            print("   [SELESAI] Header tidak ditemukan. List kosong atau menu tertutup.")
            break

        hdr_cx, hdr_cy, hdr_conf = header
        print(f"   [2] Header ditemukan ({hdr_cx}, {hdr_cy}) conf={hdr_conf:.2f}")

        # Klik item pertama
        item_x = hdr_cx
        item_y = hdr_cy + ITEM_OFFSET_Y
        print(f"   [3] Klik item ({item_x}, {item_y})...")
        device.shell(f"input tap {item_x} {item_y}")
        time.sleep(DELAY_AFTER_TAP)

        # Cari tombol Upgrade
        upgrade = find_template(TEMPLATE_UPGRADE, UPGRADE_THRESHOLD)
        if not upgrade:
            skipped += 1
            print(f"   [SKIP] Tombol Upgrade tidak ditemukan. Tutup dialog...")
            device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
            time.sleep(DELAY_AFTER_CLOSE)
            continue

        ux, uy, uconf = upgrade
        print(f"   [4] Upgrade ditemukan ({ux}, {uy}) conf={uconf:.2f}")
        device.shell(f"input tap {ux} {uy}")
        time.sleep(DELAY_AFTER_TAP)

        # Cari Confirm
        confirm = find_template(TEMPLATE_CONFIRM, CONFIRM_THRESHOLD)
        if not confirm:
            skipped += 1
            print(f"   [SKIP] Confirm tidak muncul (resource kurang?). Tutup dialog...")
            device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
            time.sleep(DELAY_AFTER_CLOSE)
            continue

        ccx, ccy, cconf = confirm
        print(f"   [5] Confirm ditemukan ({ccx}, {ccy}) conf={cconf:.2f}")
        device.shell(f"input tap {ccx} {ccy}")
        time.sleep(DELAY_AFTER_TAP)

        # Cek busy SETELAH confirm
        busy = find_template(TEMPLATE_BUSY, BUSY_THRESHOLD)
        if busy:
            busy_hit += 1
            bx, by, bconf = busy
            print(f"   [BUSY] All builders busy! (conf={bconf:.2f}) Tutup & stop.")
            device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
            time.sleep(DELAY_AFTER_CLOSE)
            break

        upgraded += 1
        print(f"   ✅ Building upgrade #{upgraded} BERHASIL!")
        logger.info(f"Building upgrade #{upgraded} berhasil")

        # Klik Builder Head lagi untuk refresh list
        print(f"   [LOOP] Klik Builder Head lagi untuk refresh...")
        device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
        time.sleep(DELAY_MENU_LOAD)

    print(f"   📊 Building: {upgraded} berhasil, {skipped} skip, {busy_hit}x busy")
    logger.info(f"Building upgrade selesai: {upgraded} berhasil, {skipped} skip")
    return upgraded

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-UPGRADE LAB                               ║
# ╚══════════════════════════════════════════════════════════════╝
def auto_upgrade_lab():
    """Upgrade lab research via Lab menu."""
    print("\n🔬 ════════════════════════════════════════")
    print("   AUTO-UPGRADE: LAB")
    print("   ════════════════════════════════════════")

    upgraded = 0
    skipped = 0
    busy_hit = 0

    # Klik Lab Icon
    print(f"   [1] Klik Lab Icon ({LAB_ICON_X}, {LAB_ICON_Y})...")
    device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
    time.sleep(DELAY_MENU_LOAD)

    while True:
        # Cek connection lost
        if handle_connection_lost():
            print("   ⚠️ Connection lost saat upgrade lab!")
            clear_popups_and_recover()
            return upgraded

        # Scan header
        header = find_template(TEMPLATE_HEADER, HEADER_THRESHOLD)
        if not header:
            print("   [SELESAI] Header tidak ditemukan. List kosong atau menu tertutup.")
            break

        hdr_cx, hdr_cy, hdr_conf = header
        print(f"   [2] Header ditemukan ({hdr_cx}, {hdr_cy}) conf={hdr_conf:.2f}")

        # Klik item pertama
        item_x = hdr_cx
        item_y = hdr_cy + ITEM_OFFSET_Y
        print(f"   [3] Klik item ({item_x}, {item_y})...")
        device.shell(f"input tap {item_x} {item_y}")
        time.sleep(DELAY_AFTER_TAP)

        # Lab: langsung cek Confirm (tidak ada tombol Upgrade)
        confirm = find_template(TEMPLATE_CONFIRM, CONFIRM_THRESHOLD)
        if not confirm:
            skipped += 1
            print(f"   [SKIP] Confirm tidak muncul (resource kurang?). Tutup dialog...")
            device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
            time.sleep(DELAY_AFTER_CLOSE)
            continue

        ccx, ccy, cconf = confirm
        print(f"   [4] Confirm ditemukan ({ccx}, {ccy}) conf={cconf:.2f}")
        device.shell(f"input tap {ccx} {ccy}")
        time.sleep(DELAY_AFTER_TAP)

        # Cek lab_busy SETELAH confirm
        lab_busy = find_template(TEMPLATE_LAB_BUSY, BUSY_THRESHOLD)
        if lab_busy:
            busy_hit += 1
            bx, by, bconf = lab_busy
            print(f"   [BUSY] Lab sedang research! (conf={bconf:.2f}) Tutup & stop.")
            device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
            time.sleep(DELAY_AFTER_CLOSE)
            break

        # Cek juga all_builders_busy (jaga-jaga)
        busy = find_template(TEMPLATE_BUSY, BUSY_THRESHOLD)
        if busy:
            busy_hit += 1
            bx, by, bconf = busy
            print(f"   [BUSY] All builders busy! (conf={bconf:.2f}) Tutup & stop.")
            device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
            time.sleep(DELAY_AFTER_CLOSE)
            break

        upgraded += 1
        print(f"   ✅ Lab upgrade #{upgraded} BERHASIL!")
        logger.info(f"Lab upgrade #{upgraded} berhasil")

        # Klik Lab Icon lagi untuk refresh list
        print(f"   [LOOP] Klik Lab Icon lagi untuk refresh...")
        device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
        time.sleep(DELAY_MENU_LOAD)

    print(f"   📊 Lab: {upgraded} berhasil, {skipped} skip, {busy_hit}x busy")
    logger.info(f"Lab upgrade selesai: {upgraded} berhasil, {skipped} skip")
    return upgraded

# ╔══════════════════════════════════════════════════════════════╗
# ║              MANAJEMEN AKUN                                 ║
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
                        device.shell("input swipe 480 400 480 150 600")
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
# ║              MASTER LOOP                                    ║
# ╚══════════════════════════════════════════════════════════════╝
def main_farming_loop():
    print()
    print("🚀 " + "=" * 53)
    print("   BOT FARM + AUTO-UPGRADE v2")
    print("=" * 55)
    print(f"    Total akun    : {len(DAFTAR_AKUN)}")
    print(f"   ▶️  Mulai dari    : Index {INDEX_AKUN_MULAI} ({DAFTAR_AKUN[INDEX_AKUN_MULAI][1]})")

    stop_str = f"Index {STOP_AFTER_INDEX} ({DAFTAR_AKUN[STOP_AFTER_INDEX][1]})" if 0 <= STOP_AFTER_INDEX < len(DAFTAR_AKUN) else "Akhir Daftar"
    print(f"   🛑 Stop di       : {stop_str}")
    print(f"    Looping       : {'Ya' if LOOP_CONTINUOUSLY else 'Tidak'}")
    print(f"   🏠 Upgrade Bldg  : {'AKTIF' if ENABLE_UPGRADE_BUILDING else 'MATI'}")
    print(f"   🔬 Upgrade Lab   : {'AKTIF' if ENABLE_UPGRADE_LAB else 'MATI'}")
    print(f"    Upgrade Mode  : {UPGRADE_MODE}")
    print("=" * 55)
    logger.info("Bot Farm+Auto v2 started")

    config = load_config()

    # 1. PINDAH KE AKUN AWAL
    scid_awal, nama_awal = DAFTAR_AKUN[INDEX_AKUN_MULAI]
    print(f"\n🔄 Switch ke akun awal: {nama_awal} (Index {INDEX_AKUN_MULAI})")

    if not switch_next_account(scid_awal):
        print(f"❌ Gagal switch ke {nama_awal}! Bot berhenti.")
        logger.error(f"Gagal switch ke {nama_awal}")
        return

    print("⏳ Menunggu village loading...")
    time.sleep(8)

    total_akun = len(DAFTAR_AKUN)
    total_battle_semua = 0
    total_upgrade_semua = 0
    start_total = time.time()

    current_index = INDEX_AKUN_MULAI
    is_first_run = True

    # ╔══════════════════════════════════════════════════════════════╗
    # ║ OUTER LOOP: Continuous                                       ║
    # ╚══════════════════════════════════════════════════════════════╝
    while True:

        # ╔══════════════════════════════════════════════════════════════╗
        # ║ INNER LOOP: Per akun                                         ║
        # ╚══════════════════════════════════════════════════════════════╝
        while current_index < total_akun:

            if STOP_AFTER_INDEX != -1 and current_index > STOP_AFTER_INDEX:
                print(f"🛑 Batas akun tercapai (Index {STOP_AFTER_INDEX}).")
                break

            scid_file, nama = DAFTAR_AKUN[current_index]

            print()
            print("" + "─" * 53 + "┐")
            print(f"│  AKUN : {nama.upper():<20} [Index {current_index}, {current_index + 1}/{total_akun}]")
            print(f"│  SCID : {scid_file}")
            print("└" + "─" * 53 + "")
            logger.info(f"=== AKUN: {nama} ({current_index}/{total_akun}) ===")

            # LOGIKA SWITCH AKUN
            if not is_first_run:
                if not switch_next_account(scid_file):
                    print(f"⚠️ Gagal pindah ke {nama}, skip...")
                    logger.warning(f"Gagal pindah ke {nama}")
                    current_index += 1
                    continue

                print("⏳ Menunggu village loading...")
                time.sleep(8)

                print("🧹 Membersihkan pop-up sebelum zoom...")
                clear_popups_and_recover()
                time.sleep(1)
            else:
                print("🧹 Membersihkan pop-up awal sebelum zoom...")
                clear_popups_and_recover()
                time.sleep(1)
                is_first_run = False

            # ZOOM OUT
            try:
                zoom_ctrl.zoom_out()
            except Exception as e:
                print(f"   ⚠️ Zoom error: {e}, lanjut tanpa zoom")
                logger.error(f"Zoom error: {e}")
                save_debug_screenshot("zoom_error")
            time.sleep(1)

            # CEK DE & STORAGE
            punya_de = get_punya_de(scid_file, config)
            if punya_de is not None and not FORCE_REDETECT_DE:
                print(f"   📋 DE dari cache: {'Ada' if punya_de else 'Tidak ada'}")
            else:
                print(f"    Auto-detect DE...")
                punya_de = detect_de_availability()
                config[scid_file] = {"punya_de": punya_de}
                save_config(config)
                print(f"   💾 Disimpan ke config")

            gold_full, elixir_full, de_full = cek_status_resource(punya_de)
            print(format_resource_status(gold_full, elixir_full, de_full, punya_de))
            storage_penuh = is_storage_penuh(gold_full, elixir_full, de_full, punya_de)

            # ═══════════════════════════════════════════════════════
            # LOGIKA FARM + UPGRADE
            # ═══════════════════════════════════════════════════════

            # ── STEP A: FARMING ──
            if not storage_penuh:
                print(f"\n   🌾 Storage belum penuh → FARMING...")
                start_sesi = time.time()
                battle_count = 0
                army_loaded = False

                while True:
                    army_loaded = battle_sequence(army_loaded=army_loaded)
                    battle_count += 1
                    total_battle_semua += 1
                    print(f"\n   ⚔️ Battle #{battle_count} [{nama}] selesai")
                    logger.info(f"Battle #{battle_count} [{nama}] selesai")

                    time.sleep(2)
                    handle_connection_lost()
                    clear_popups_and_recover()
                    time.sleep(1)

                    gold_full, elixir_full, de_full = cek_status_resource(punya_de)
                    print(format_resource_status(gold_full, elixir_full, de_full, punya_de))

                    if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                        print(f"   ✅ Storage PENUH setelah {battle_count} battle!")
                        break

                    elapsed = time.time() - start_sesi
                    if elapsed > MAKSIMAL_WAKTU_PER_AKUN:
                        print(f"   ⏱️ Safety net {MAKSIMAL_WAKTU_PER_AKUN // 60}m!")
                        break

                    menit = int(elapsed // 60)
                    detik = int(elapsed % 60)
                    sisa = MAKSIMAL_WAKTU_PER_AKUN - elapsed
                    print(f"   ⏱️ Farming: {menit}m {detik}s | Sisa: {int(sisa // 60)}m {int(sisa % 60)}s")
                    time.sleep(2)
            else:
                print(f"\n   ⚠️ Storage sudah PENUH → skip farming")

            # ── STEP B: UPGRADE ──
            if ENABLE_UPGRADE_BUILDING or ENABLE_UPGRADE_LAB:
                print(f"\n   🔧 Memulai auto-upgrade (Mode {UPGRADE_MODE})...")
                clear_popups_and_recover()
                time.sleep(1)

                if ENABLE_UPGRADE_BUILDING:
                    b_up = auto_upgrade_building()
                    total_upgrade_semua += b_up
                else:
                    b_up = 0
                    print("   ⏭️ Building upgrade: SKIP (mati)")

                device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
                time.sleep(DELAY_AFTER_CLOSE)

                if ENABLE_UPGRADE_LAB:
                    l_up = auto_upgrade_lab()
                    total_upgrade_semua += l_up
                else:
                    l_up = 0
                    print("   ⏭️ Lab upgrade: SKIP (mati)")

                device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
                time.sleep(DELAY_AFTER_CLOSE)

                print(f"   📊 Total upgrade akun ini: {b_up} building + {l_up} lab")

                # ── STEP C: MODE 2 → Farm lagi ──
                if UPGRADE_MODE == 2:
                    clear_popups_and_recover()
                    time.sleep(1)
                    gold_full, elixir_full, de_full = cek_status_resource(punya_de)
                    print(format_resource_status(gold_full, elixir_full, de_full, punya_de))

                    if not is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                        print(f"\n   🌾 Mode 2: Farming lagi setelah upgrade...")
                        start_sesi2 = time.time()
                        battle_count2 = 0

                        while True:
                            battle_sequence(army_loaded=True)
                            battle_count2 += 1
                            total_battle_semua += 1
                            print(f"\n   ⚔️ Battle #{battle_count2} [{nama}] post-upgrade selesai")

                            time.sleep(2)
                            handle_connection_lost()
                            clear_popups_and_recover()
                            time.sleep(1)

                            gold_full, elixir_full, de_full = cek_status_resource(punya_de)
                            print(format_resource_status(gold_full, elixir_full, de_full, punya_de))

                            if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                                print(f"   ✅ Storage PENUH post-upgrade!")
                                break

                            elapsed2 = time.time() - start_sesi2
                            if elapsed2 > MAKSIMAL_WAKTU_PER_AKUN:
                                print(f"   ⏱️ Safety net post-upgrade!")
                                break

                            menit2 = int(elapsed2 // 60)
                            detik2 = int(elapsed2 % 60)
                            print(f"   ⏱️ Post-upgrade: {menit2}m {detik2}s")
                            time.sleep(2)
                    else:
                        print(f"   ⚠️ Mode 2: Storage masih penuh, skip")

            # ═══════════════════════════════════════════════════════
            # ── AKHIR SESI AKUN INI ──
            # ═══════════════════════════════════════════════════════
            print(f"   ✅ Akun {nama} selesai!")

            current_index += 1

        # ═══════════════════════════════════════════════════════════
        # AKHIR INNER LOOP
        # ═══════════════════════════════════════════════════════════

        if not LOOP_CONTINUOUSLY:
            print(" Looping dimatikan. Bot berhenti.")
            break

        print(" Mengulang dari akun awal...")
        current_index = 0
        is_first_run = False
        time.sleep(5)

    # ═══════════════════════════════════════════════════════════
    # LAPORAN AKHIR
    # ═══════════════════════════════════════════════════════════
    total_waktu = time.time() - start_total
    menit_total = int(total_waktu // 60)
    detik_total = int(total_waktu % 60)

    print()
    print("=" * 55)
    print("   🎉 MISI SELESAI!")
    print("=" * 55)
    print(f"   📊 Total battle  : {total_battle_semua}")
    print(f"    Total upgrade : {total_upgrade_semua}")
    print(f"   📋 Total akun    : {len(DAFTAR_AKUN)}")
    print(f"   ⏱️ Total waktu   : {menit_total}m {detik_total}s")
    print("=" * 55)
    logger.info(f"Bot selesai: {total_battle_semua} battle, {total_upgrade_semua} upgrade, {menit_total}m")

    # ── BARU DISINI press home + minimize ──
    press_home()
    time.sleep(1)
    close_ldplayer()
    print("   🖥️ LDPlayer minimized. Bye!")

if __name__ == "__main__":
    main_farming_loop()