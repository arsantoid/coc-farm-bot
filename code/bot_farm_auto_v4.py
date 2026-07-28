import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["GOTO_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_MAX_THREADS"] = "1"
import cv2
import numpy as np
import time
import random
import json
import ctypes
import logging
import subprocess
import tempfile
from ppadb.client import Client as AdbClient
import reconnect_adb

# safe screencap wrapper - auto-reconnect on failure
def safe_screencap():
    global device, client
    for _att in range(3):
        try:
            sc = device.screencap()
            if sc and len(sc) > 100:
                return sc
        except Exception as e:
            print(f"Screencap fail (attempt {_att+1}): {e}")
            ok, client, device = reconnect_adb.reconnect_adb()
            if ok:
                import time
                time.sleep(2)
    return None

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
    ("scid_example.png",    "example"), 
]


# ╔══════════════════════════════════════════════════════════════╗
# ║              KONFIGURASI GLOBAL                             ║
# ╚══════════════════════════════════════════════════════════════╝
INDEX_AKUN_MULAI = 0
STOP_AFTER_INDEX = -1
LOOP_CONTINUOUSLY = True
MAKSIMAL_WAKTU_PER_AKUN = 3600
FORCE_REDETECT_DE = False
MACRO_WAIT = 6

# ── SPELL DEPLOYMENT (Tengah Village) ──
SPELL_COORDS_1 = [
    (480, 270), (430, 220), (530, 220), (430, 320), (530, 320),
]
SPELL_COORDS_2 = [
    (480, 220), (480, 320), (430, 270),
]

# ── EVENT TROOP ──
EVENT_TROOP_DEFS = []
EVENT_TROOP_COORDS = []
EVENT_TROOP_SWIPE_DURATION = 3500

# ── EVENT SPELL ──
EVENT_SPELL_DEFS = [
    "spell_rage.png",
    "spell_freeze.png",
]
EVENT_SPELL_COORDS = [
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
EVENT_SPELL_MAX_TAPS = 100

# ── DEPLOY ──
LOOT_WAIT_MIN = 20
LOOT_WAIT_MAX = 30

# ── CONNECTION LOST ──
LOADING_TIMEOUT = 10
MATCH_FIND_TIMEOUT = 5
SEARCHING_TIMEOUT = 60
TEMPLATE_SEARCHING = "searching_opponents.png"

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-UPGRADE CONFIG (v3 TARGETED)              ║
# ╚══════════════════════════════════════════════════════════════╝
ENABLE_UPGRADE_BUILDING = True
ENABLE_UPGRADE_LAB = True
ENABLE_FALLBACK_TO_SUGGESTED = False
MAX_FARM_UPGRADE_CYCLES = 3

BUILDER_HEAD_X = 450
BUILDER_HEAD_Y = 25
LAB_ICON_X = 325
LAB_ICON_Y = 30

CLOSE_X = 900
CLOSE_Y = 40

DELAY_AFTER_TAP = 1.0      # dari 1.5
DELAY_AFTER_CLOSE = 0.7     # dari 1.0
DELAY_MENU_LOAD = 2.0       # dari 3.0

# ── MENU AREA (Suggested Upgrades) ──
MENU_LEFT = 357
MENU_RIGHT = 620
MENU_TOP = 88
MENU_BOTTOM = 400
SCROLL_X = (MENU_LEFT + MENU_RIGHT) // 2
SCROLL_Y_TOP = MENU_TOP + 30
SCROLL_Y_BOTTOM = MENU_BOTTOM - 30
SCROLL_SPEED = 2000
MAX_SCROLLS = 8

# ── THRESHOLDS ──
DETECT_THRESHOLD = 0.85
CONFIRM_THRESHOLD = 0.80
UPGRADE_THRESHOLD = 0.75
BUSY_THRESHOLD = 0.85
HEADER_THRESHOLD = 0.70
CANCEL_THRESHOLD = 0.80
FINISH_NOW_THRESHOLD = 0.80
UIP_THRESHOLD = 0.80
HEY_CHIEF_THRESHOLD = 0.80

# ── MULTI-SCALE ──
MULTI_SCALES = [0.98, 1.0, 1.02]   # coba beberapa skala untuk anti-zoom

# ── TEMPLATE FILES ──
TEMPLATE_HEADER = "suggested_upgrades_text.png"
TEMPLATE_UPGRADE = "upgrade_btn_dim.png"
TEMPLATE_UPGRADE_BOLD = "upgrade_btn.png"
TEMPLATE_CONFIRM = "confirm_text.png"
TEMPLATE_BUSY = "all_builders_busy.png"
TEMPLATE_LAB_BUSY = "lab_busy.png"
TEMPLATE_CANCEL_DIM = "cancel_upgrade_dim.png"
TEMPLATE_CANCEL_BOLD = "cancel_upgrade_bold.png"
TEMPLATE_FINISH_NOW = "finish_now.png"
TEMPLATE_UPGRADE_IN_PROGRESS = "upgrade_in_progress.png"
TEMPLATE_HEY_CHIEF = "hey_chief.png"


CONFIRM_TEMPLATES_HERO = [
    "btn_up_hero.png",
    "btn_up_hero_de.png",
    "confirm_text.png",
]

CONFIRM_TEMPLATES_LAB = [
    "btn_lab_confirm.png",
    "btn_lab_confirm_de.png",
    "confirm_text.png",
]

CONFIRM_TEMPLATES_BUILDING = [
    "btn_up_building_elixir.png",
    "btn_up_building_gold.png",
    "confirm_text.png",
]

CONFIRM_TEMPLATES_ALL = [
    "confirm_text.png",
    "btn_lab_confirm.png",
    "btn_lab_confirm_de.png",
    "btn_up_building_elixir.png",
    "btn_up_building_gold.png",
    "btn_up_hero.png",
    "btn_up_hero_de.png",
]
# ── BUILDING TEMPLATES (targeted upgrade) ──
# priority: 1 = paling atas, 2 = berikutnya, dst. 0 = normal (terakhir)
# is_hero: True = hero (cek finish_now), False = building (cek cancel)
BUILDING_TEMPLATES = [
    # ("building_barbarian_king.png",      "Barbarian King",      True,  0),
    # ("building_archer_queen.png",        "Archer Queen",        True,  0),
    # ("building_royal_champion.png",      "Royal Champion",      True,  0),
    # ("building_minion_prince.png",       "Minion Prince",       True,  0),
    # ("building_grand_warden.png",        "Grand Warden",        True,  0),
    
    ("building_lab.png",                 "Laboratorium",        False, 1),
    ("building_clan_castle.png",         "Clan Castle",         False, 1),
    ("building_hero_hall.png",           "Hero Hall",           False, 1),
    ("building_blacksmith.png",          "Blacksmith",          False, 2),
    ("building_spell_factory.png",       "Spell Factory",       False, 2),
    ("building_elixir_storage.png",      "Elixir Storage",      False, 2),
    ("building_gold_storage.png",        "Gold Storage",        False, 2),
    ("building_dark_elixir_storage.png", "Dark Elixir Storage", False, 2),
    # ("building_army_camp.png",           "Army Camp",           False, 3),
    # ("building_dark_barracks.png",       "Dark Barracks",       False, 3),
    # ("building_dark_spell_factory.png",  "Dark Spell Factory",  False, 4),
    # ("building_barracks.png",            "Barracks",            False, 4),
    # ("building_workshop.png",            "Workshop",            False, 4),
    # ("building_pet_house.png",           "Pet House",           False, 4),

    
    # ("building_eagle_artillery.png",     "Eagle Artillery",     False, 0),
    
    # ("building_townhall.png",           "Town Hall",           False, 0),
    # ("building_builder_hut.png",         "Builder's Hut",       False, 0),
    # ("building_scattershhot.png",        "Scattershot",         False, 0),
    # ("building_elixir_collector.png",    "Elixir Collector",    False, 0),
    # ("building_gold_mine.png",           "Gold Mine",           False, 0),
    # ("building_dark_elixir_drill.png",   "Dark Elixir Drill",   False, 0),
]

# ── LAB TEMPLATES (targeted upgrade) ──
# priority: 1 = paling atas, 0 = normal
# Tambah sesuai screenshot research item di lab
LAB_TEMPLATES = [
    ("lab_dragon.png",              "Dragon",          1),
    # ("lab_archer.png",              "Archer",          2),
    # ("lab_minion.png",              "Minion",          2),
    # ("lab_barbarian.png",           "Barbarian",       3),
    # ("lab_freeze_spell.png",        "Freeze Spell",    3),
    # ("lab_giant.png",      "Giant",      0),
]

# ╔══════════════════════════════════════════════════════════════╗
# ║              TEMPLATE CACHE (RAM)                           ║
# ╚══════════════════════════════════════════════════════════════╝
_template_cache = {}

def load_template(template_name):
    """Load template dari cache atau disk. Return numpy array atau None."""
    if template_name in _template_cache:
        return _template_cache[template_name]
    img_path = os.path.join(GAMBAR_DIR, template_name)
    if not os.path.exists(img_path):
        _template_cache[template_name] = None
        return None
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    _template_cache[template_name] = img
    return img

# ╔══════════════════════════════════════════════════════════════╗
# ║              STATE PERSISTENCE (di account_config.json)     ║
# ╚══════════════════════════════════════════════════════════════╝
def save_progress(account_index, account_name):
    """Simpan posisi terakhir ke account_config.json."""
    config = load_config()
    config["_last_progress"] = {
        "account_index": account_index,
        "account_name": account_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_config(config)
    print(f"   💾 Progress disimpan: {account_name} (index {account_index})")
    logger.info(f"Progress saved: {account_name} (index {account_index})")

def load_progress():
    """Baca posisi terakhir dari account_config.json. Return (index, name) atau (None, None)."""
    config = load_config()
    prog = config.get("_last_progress")
    if prog and "account_index" in prog:
        return prog["account_index"], prog.get("account_name", "?")
    return None, None

def clear_progress():
    """Hapus _last_progress dari account_config.json."""
    config = load_config()
    if "_last_progress" in config:
        del config["_last_progress"]
        save_config(config)
        print("   🗑️ Progress dihapus (semua akun selesai)")
        

def find_confirm_button_on_screen(screen, context="all", threshold=CONFIRM_THRESHOLD):
    if context == "hero":
        templates = CONFIRM_TEMPLATES_HERO
    elif context == "lab":
        templates = CONFIRM_TEMPLATES_LAB
    elif context == "building":
        templates = CONFIRM_TEMPLATES_BUILDING
    else:
        templates = CONFIRM_TEMPLATES_ALL

    for tpl in templates:
        result = find_on_screen(tpl, screen, threshold, scales=MULTI_SCALES)
        if result:
            print(f"   ✅ Confirm [{context}]: {tpl} ({result[2]:.2f})")
            return result
    return None

# ╔══════════════════════════════════════════════════════════════╗
# ║              KONEKSI ADB (auto-detect)                      ║
# ╚══════════════════════════════════════════════════════════════╝
def _auto_detect_adb():
    """Auto-detect ADB server port and emulator device.
    
    Strategy: DON'T start/kill ADB servers (that breaks BlueStacks).
    Just find standard adb.exe, connect to emulator, and let ppadb use port 5037.
    """
    import subprocess, socket

    # 1. Find standard adb.exe
    import shutil
    import os
    user_profile = os.environ.get("USERPROFILE", "C:\\")
    adb_candidates = [
        os.path.join(user_profile, "platform-tools", "adb.exe"),
        os.path.join(user_profile, "AppData", "Local", "Android", "Sdk", "platform-tools", "adb.exe"),
        r"C:\Android\platform-tools\adb.exe",
    ]
    path_adb = shutil.which("adb")
    if path_adb:
        adb_candidates.insert(0, path_adb)

    adb_path = None
    for p in adb_candidates:
        if os.path.isfile(p):
            adb_path = p
            break
    if not adb_path:
        ld_paths = [
            r"C:\LDPlayer\LDPlayer9\adb.exe",
            r"C:\Program Files\LDPlayer\LDPlayer9\adb.exe",
        ]
        for p in ld_paths:
            if os.path.isfile(p):
                adb_path = p
                break
    if not adb_path:
        return None, None, None

    # 2. DON'T kill anything - just connect to running emulator
    # Scan common ports
    emulator_ports = []
    for port in range(5555, 5570):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            emulator_ports.append(port)
        s.close()

    # Connect to found ports (this registers them with whatever ADB server is on 5037)
    for port in emulator_ports:
        addr = f"127.0.0.1:{port}"
        subprocess.run([adb_path, "connect", addr], capture_output=True)
        time.sleep(0.5)

    # Check via adb devices
    result = subprocess.run([adb_path, "devices"], capture_output=True, text=True)
    connected_devices = []
    for line in result.stdout.strip().split("\n")[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            connected_devices.append(parts[0])

    # Also check emulator-XXXX style (LDPlayer native)
    result2 = subprocess.run([adb_path, "devices"], capture_output=True, text=True)
    for line in result2.stdout.strip().split("\n")[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device" and parts[0] not in connected_devices:
            connected_devices.append(parts[0])

    return adb_path, connected_devices, emulator_ports

print("🔍 Auto-detecting ADB & emulator...")
adb_path, devices_found, ports_found = _auto_detect_adb()

if not devices_found:
    print("❌ Emulator tidak terdeteksi oleh ADB!")
    print("   Pastikan emulator (BlueStacks/LDPlayer/MEmu) sedang jalan.")
    logger.error("Emulator tidak terdeteksi!")
    exit()

# Use standard ADB server port 5037
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
if len(devices) == 0:
    print("❌ ADB server tidak melihat device!")
    print(f"   Found ports: {ports_found}, device strings: {devices_found}")
    logger.error("ADB server tidak melihat device!")
    exit()
device = devices[0]
print(f"✅ Terhubung ke emulator: {device.serial}")
logger.info(f"Terhubung ke emulator: {device.serial}")

def launch_coc():
    """Buka Clash of Clans dari kondisi apapun menggunakan ADB."""
    try:
        # Method 1: am start with various activity names
        for activity in [
            "com.supercell.clashofclans/com.supercell.titan.GameApp",
            "com.supercell.clashofclans/.GameApp",
            "com.supercell.clashofclans/com.supercell.clashofclans.GameApp",
        ]:
            result = device.shell(f"am start -n {activity}")
            if "Error" not in result and "exception" not in result.lower():
                print("   📱 Launching CoC (am start)...")
                time.sleep(8)
                if is_coc_running():
                    return True

        # Method 2: monkey launcher (most reliable)
        device.shell("monkey -p com.supercell.clashofclans -c android.intent.category.LAUNCHER 1")
        print("   📱 Launching CoC (monkey)...")
        time.sleep(10)
        if is_coc_running():
            return True

        # Method 3: am start with action
        device.shell("am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.supercell.clashofclans/com.supercell.titan.GameApp")
        time.sleep(8)
        if is_coc_running():
            return True

        print("   ⚠️ Gagal launch CoC (semua method gagal)")
        return False
    except Exception as e:
        print(f"   ⚠️ Gagal launch CoC: {e}")
        return False

def is_coc_running():
    """Check apakah CoC sedang running sebagai foreground app."""
    try:
        result = device.shell("dumpsys activity activities | grep mResumedActivity")
        if "clashofclans" in result.lower() or "supercell" in result.lower():
            return True
        # Also check top activity
        result2 = device.shell("dumpsys window | grep mCurrentFocus")
        if "clashofclans" in result2.lower():
            return True
        return False
    except:
        return False

def is_coc_installed():
    """Check apakah CoC terinstal di emulator."""
    try:
        result = device.shell("pm list packages | grep clashofclans")
        return "clashofclans" in result
    except:
        return False

def ensure_coc_running():
    """Pastikan CoC running. Restart jika force-close. Return True jika OK."""
    if is_coc_running():
        return True
    print("   ⚠️ CoC tidak running! Restarting...")
    logger.warning("CoC not running, restarting")
    if not launch_coc():
        print("   ❌ Gagal restart CoC!")
        return False
    # Wait and verify
    time.sleep(5)
    for attempt in range(3):
        if is_coc_running():
            print("   ✅ CoC restarted successfully!")
            clear_popups_and_recover()
            return True
        print(f"   ⏳ Waiting for CoC... (attempt {attempt+1}/3)")
        time.sleep(5)
    print("   ❌ CoC gagal start setelah 3 percobaan!")
    return False

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
# ║              ACCOUNT STATE MANAGEMENT (v5)                  ║
# ╚══════════════════════════════════════════════════════════════╝

def get_account_state(scid_file):
    """Ambil state akun dari config. Return dict atau None jika belum ada."""
    config = load_config()
    if scid_file in config:
        return config[scid_file].get("state", {})
    return None

def update_account_state(scid_file, **kwargs):
    """Update field state untuk akun tertentu. Simpan otomatis."""
    config = load_config()
    if scid_file not in config:
        config[scid_file] = {}
    if "state" not in config[scid_file]:
        config[scid_file]["state"] = {}
    for key, value in kwargs.items():
        config[scid_file]["state"][key] = value
    config[scid_file]["state"]["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_config(config)

def reset_account_state(scid_file):
    """Reset state akun (hapus semua data progres)."""
    config = load_config()
    if scid_file in config and "state" in config[scid_file]:
        del config[scid_file]["state"]
        save_config(config)
        print(f"   🗑️ State reset untuk {scid_file}")

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEBUG SCREENSHOT                               ║
# ╚══════════════════════════════════════════════════════════════╝
def save_debug_screenshot(label="error"):
    try:
        screencap = safe_screencap()
        if screencap is None:
            return None
        img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
        filename = f"{label}_{int(time.time())}.png"
        path = os.path.join(DEBUG_DIR, filename)
        cv2.imwrite(path, img)
        print(f"📸 Debug: {filename}")
        logger.info(f"Debug screenshot: {filename}")
    except Exception as e:
        print(f"⚠️ Gagal screenshot debug: {e}")

# ╔══════════════════════════════════════════════════════════════╗
# ║              SCREENSHOT & TAP HELPERS                       ║
# ╚══════════════════════════════════════════════════════════════╝
def take_screenshot():
    global device, client
    for _att in range(3):
        try:
            screencap = safe_screencap()
            if screencap and len(screencap) > 100:
                return cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Screenshot fail (attempt {_att+1}): {e}")
            if _att < 2:
                from reconnect_adb import reconnect_adb
                ok, client, device = reconnect_adb()
                if not ok:
                    break
                time.sleep(2)
    print("Screenshot gagal - reconnect needed")
    return None

def tap(x, y, offset=5):
    device.shell(f"input tap {x + random.randint(-offset, offset)} {y + random.randint(-offset, offset)}")

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-DETECT DE                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_de_availability():
    screencap = safe_screencap()
    if screencap is None:
        return None
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
                if "bluestacks" in title.lower():
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
            f.write('s.AppActivate "BlueStacks"\n')
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
# ║              TEMPLATE MATCHING                              ║
# ╚══════════════════════════════════════════════════════════════╝
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

def find_on_screen(template_name, screen, threshold=0.85, scales=None):
    """
    Cari template di screenshot dengan multi-scale matching.
    scales: list float, misal [0.98, 1.0, 1.02]. Default [1.0].
    Return (x, y, confidence) atau None.
    """
    template = load_template(template_name)
    if template is None:
        return None

    if scales is None:
        scales = [1.0]

    if not os.path.isfile(template_path):
        print(f"   ⚠️ {template_name} tidak ditemukan!")
        return None
    tpl = cv2.imread(template_path)
    if tpl is None:
        print(f"   ⚠️ Gagal load {template_name}")
        return None
    if tpl.shape[1] > screen_img.shape[1] or tpl.shape[0] > screen_img.shape[0]:
        return None

    best = None
    best_conf = -1.0
    th, tw = tpl.shape[:2]

    for scale in [1.0]:
        if scale != 1.0:
            new_w = int(tw * scale)
            new_h = int(th * scale)
            if new_w < 1 or new_h < 1:
                continue
            tpl_scaled = cv2.resize(tpl, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        else:
            tpl_scaled = tpl

        th_s, tw_s = tpl_scaled.shape[:2]
        if th_s >= screen_img.shape[0] or tw_s >= screen_img.shape[1]:
            continue

        import gc
        gc.collect()
        result = cv2.matchTemplate(screen_img, tpl_scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold and max_val > best_conf:
            best_conf = max_val
            cx = max_loc[0] + (tw_s // 2)
            cy = max_loc[1] + (th_s // 2)
            best = (cx, cy, max_val)

    return best


def find_template(template_name, threshold=0.85, scales=None):
    """Sama seperti find_on_screen, tapi mengambil screenshot sendiri."""
    template = load_template(template_name)
    if template is None:
        return None

    screencap = safe_screencap()
    if screencap is None:
        return None
    screen_img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

    if scales is None:
        scales = [1.0]

    best = None
    best_conf = -1

    for scale in scales:
        if scale == 1.0:
            tpl = template
        else:
            h, w = template.shape[:2]
            new_w = int(w * scale)
            new_h = int(h * scale)
            if new_w < 1 or new_h < 1:
                continue
            tpl = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        th, tw = tpl.shape[:2]
        if th >= screen_img.shape[0] or tw >= screen_img.shape[1]:
            continue

        import gc
        gc.collect()
        result = cv2.matchTemplate(screen_img, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold and max_val > best_conf:
            best_conf = max_val
            cx = max_loc[0] + (tw // 2)
            cy = max_loc[1] + (th // 2)
            best = (cx, cy, max_val)

    return best

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-DETECT TROOP SLOTS                        ║
# ╚══════════════════════════════════════════════════════════════╝
def detect_troop_slots():
    empty_template = load_template("empty_slot.png")
    if empty_template is None:
        print("   ⚠️ empty_slot.png tidak ada! Assume semua terisi.")
        return [True] * 11
    screencap = safe_screencap()
    if screencap is None:
        return None
    screen = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

    tw = empty_template.shape[1]
    START_X = 110  # Digeser ke kiri agar slot paling kiri ikut (sebelumnya 168)
    TOTAL_SLOTS = 12 # Tambah jadi 12 slot
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
        elif max_sim < 0.40:
            is_filled = True
        elif color_var >= 30:
            is_filled = True
        else:
            is_filled = False

        slots.append(is_filled)

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
    print("   🏋️ Loading saved army preset...")
    time.sleep(1)
    device.shell(f"input tap {SAVED_RECIPE_X} {SAVED_RECIPE_Y}")
    time.sleep(1.5)
    device.shell(f"input tap {USE_ARMY_X} {USE_ARMY_Y}")
    time.sleep(2)
    print("   ✅ Saved army loaded!")

# ╔══════════════════════════════════════════════════════════════╗
# ║              DETEKSI BAR                                    ║
# ╚══════════════════════════════════════════════════════════════╝
def find_in_bar(template_file):
    """Cari template di bar bawah (troop/spell slots). Pakai cache RAM."""
    template = load_template(template_file)
    if template is None:
        return None

    h, w = template.shape[:2]
    screencap = safe_screencap()
    if screencap is None:
        return None
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
# ║              DEPLOY SPELL (SLOT-BASED)                      ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_spells_by_slots(spell_slot_indices):
    if not spell_slot_indices:
        return 0

    START_X = 110  # Samakan dengan detect_troop_slots
    GAP_X = 58
    TAP_Y = 495

    total = 0
    for idx, si in enumerate(spell_slot_indices):
        slot_x = START_X + (si * GAP_X) + (GAP_X // 2)
        device.shell(f"input tap {slot_x} {TAP_Y}")
        time.sleep(0.2)

        # Ganjil → COORDS_1 (5 tap), Genap → COORDS_2 (3 tap)
        if idx % 2 == 0:
            coords = SPELL_COORDS_2
            tipe = "3x"
        else:
            coords = SPELL_COORDS_1
            tipe = "5x"

        taps = 0
        for cx, cy in coords:
            tx = cx + random.randint(-15, 15)
            ty = cy + random.randint(-15, 15)
            device.shell(f"input tap {tx} {ty}")
            taps += 1
            total += 1
            time.sleep(0.2)

        print(f"   🔮 Spell slot {si} ({idx + 1}/{len(spell_slot_indices)}) → {taps}x [{tipe}]")

    if total > 0:
        print(f"   ✅ {total} spell taps dari {len(spell_slot_indices)} slot!")
        logger.info(f"Spells: {total} taps dari {len(spell_slot_indices)} slot")
    return total

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY EVENT TROOPS                            ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_event_troops():
    if not EVENT_TROOP_DEFS:
        return 0

    total = 0
    for troop_file in EVENT_TROOP_DEFS:
        troop_pos = find_in_bar(troop_file)
        if not troop_pos:
            continue

        tx, ty, conf = troop_pos
        device.shell(f"input tap {tx} {ty}")
        time.sleep(0.3)

        for bx, by in EVENT_TROOP_COORDS:
            jx = bx + random.randint(-15, 15)
            jy = by + random.randint(-10, 10)
            device.shell(f"input swipe {jx} {jy} {jx} {jy} {EVENT_TROOP_SWIPE_DURATION}")
            total += 1
            time.sleep(0.2)

        print(f"   🎪 Event troop {troop_file} ({conf:.2f}) → {len(EVENT_TROOP_COORDS)}x swipe")

    if total > 0:
        print(f"   ✅ {total} event troop deployments!")
    return total

# ╔══════════════════════════════════════════════════════════════╗
# ║              DEPLOY EVENT SPELLS                            ║
# ╚══════════════════════════════════════════════════════════════╝
def deploy_event_spells():
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
    return total_taps

# ╔══════════════════════════════════════════════════════════════╗
# ║              POPUP & RESOURCE                               ║
# ╚══════════════════════════════════════════════════════════════╝
def clear_event_popups():
    cleared = 0
    for _ in range(5):  # cukup 5 kali
        found = False

        if find_and_click("claim_reward_event.png", threshold=0.80):
            print(f"   🎁 Claim Reward! (ke-{cleared + 1})")
            time.sleep(1.5)  # dikurangi dari 2
            if find_and_click("event_continue.png", threshold=0.85):
                print(f"   🎁 Event Continue!")
                time.sleep(1.5)
            cleared += 1
            found = True

        if not found and find_and_click("event_continue.png", threshold=0.85):
            print(f"   🎁 Event Continue! (ke-{cleared + 1})")
            time.sleep(1.5)
            cleared += 1
            found = True

        if not found and find_and_click("event_skip.png", threshold=0.85):
            print(f"   🎁 Event Skip! (ke-{cleared + 1})")
            time.sleep(1.5)
            cleared += 1
            found = True

        if not found:
            break

    # Tap X cukup sekali di luar loop
    for _ in range(4):
        device.shell(f"input tap {random.randint(920,930)} {random.randint(56,57)}")
        time.sleep(0.3)  # lebih cepat

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
    # Check if CoC crashed (force-close)
    if not is_coc_running():
        print("   💀 CoC force-closed! Restarting...")
        logger.warning("CoC force-closed, restarting")
        return ensure_coc_running()

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
    if zoom_ctrl.hwnd_ld:
        zoom_ctrl.user32.ShowWindow(zoom_ctrl.hwnd_ld, 6)
        print("   🖥️ LDPlayer minimized!")
        logger.info("LDPlayer minimized")
    else:
        print("   ⚠️ LDPlayer window tidak ditemukan, skip minimize")

def press_home():
    device.shell("input keyevent 3")
    time.sleep(1)
    print("   🏠 Home button ditekan!")
    logger.info("Home button pressed")

# ╔══════════════════════════════════════════════════════════════╗
# ║              RESOURCE CHECK                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def cek_status_resource(punya_de=True):
    print("🔍 Mengecek kapasitas Storage...")
    screencap = safe_screencap()
    if screencap is None:
        return None
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
# ║              CAMERA                                         ║
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
    ("hero_king.png",       10),
    ("hero_queen.png",      2),
    ("hero_warden.png",     8),
    ("hero_minion.png",     12),
    ("hero_rc.png",         8),
]

SIEGE_DEFS = []

def _find_slot_index(bar_x):
    START_X = 168
    SLOT_W = 58
    idx = int((bar_x - START_X) / SLOT_W)
    return max(0, min(idx, 10))

def detect_special_slots():
    hero_indices = {}
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

    START_X = 110
    GAP_X = 58
    TAP_Y = 495
    titik_lompat = [(350, 80), (600, 85)]

    slots = detect_troop_slots()
    total_terisi = sum(slots)
    hero_slots, siege_slots = detect_special_slots()

    if hero_slots:
        boundary = max(hero_slots.keys())
    elif siege_slots:
        boundary = max(siege_slots)
    else:
        filled = [i for i, t in enumerate(slots) if t]
        boundary = max(filled) if filled else -1

    spell_slot_indices = [i for i in range(boundary + 1, 12) if slots[i]]
    troop_indices = [i for i, t in enumerate(slots) if t and i not in spell_slot_indices]

    print(f"   📊 {total_terisi} slot | Hero: {list(hero_slots.keys())} | Siege: {siege_slots} | Spell: {spell_slot_indices}")

    event_troop_count = deploy_event_troops()

    deployed_count = 0
    hero_deploy_info = []

    for i in troop_indices:
        slot_x = START_X + (i * GAP_X) + (GAP_X // 2)
        device.shell(f"input tap {slot_x} {TAP_Y}")
        time.sleep(0.1)

        if i in hero_slots:
            for base_x, base_y in titik_lompat:
                hx = base_x + random.randint(-15, 15)
                hy = base_y + random.randint(-10, 10)
                device.shell(f"input tap {hx} {hy}")
                time.sleep(0.3)
            hero_deploy_info.append((slot_x, hero_slots[i]))
            print(f"   🦸 Hero slot {i} deployed! (delay={hero_slots[i]}s)")

        elif i in siege_slots:
            sx = 480 + random.randint(-50, 50)
            sy = 270 + random.randint(-50, 50)
            device.shell(f"input tap {sx} {sy}")
            print(f"   🚗 Siege slot {i} deployed!")
            time.sleep(0.3)

        else:
            for base_x, base_y in titik_lompat:
                jx = base_x + random.randint(-15, 15)
                jy = base_y + random.randint(-10, 10)
                device.shell(f"input swipe {jx} {jy} {jx} {jy} 2200")
            time.sleep(0.3)

        deployed_count += 1
        print(f"   ✅ Slot {i} ({deployed_count}/{len(troop_indices)})")

    if hero_deploy_info:
        max_delay = max(delay for _, delay in hero_deploy_info)
        print(f"   🦸 {len(hero_deploy_info)} hero. Max delay: {max_delay}s")
        
        # Mulai timer
        start_time = time.time()
        ability_activated = [False] * len(hero_deploy_info)
        
        # ── Deploy event spells & normal spells dengan pengecekan ability ──
        event_spell_count = 0
        normal_spell_count = 0
        
        # Deploy event spells (dengan interrupt ability)
        if EVENT_SPELL_DEFS:
            for spell_file in EVENT_SPELL_DEFS:
                total_taps = 0
                while total_taps < EVENT_SPELL_MAX_TAPS:
                    # Cek ability setiap 5 tap
                    if total_taps % 5 == 0:
                        elapsed = time.time() - start_time
                        for idx, (slot_x, delay) in enumerate(hero_deploy_info):
                            if not ability_activated[idx] and elapsed >= delay:
                                device.shell(f"input tap {slot_x} {TAP_Y}")
                                print(f"   ⚡ Hero ability! (x={slot_x})")
                                ability_activated[idx] = True
                    
                    # Ambil koordinat acak untuk event spell
                    cx, cy = random.choice(EVENT_SPELL_COORDS)
                    tx = cx + random.randint(-20, 20)
                    ty = cy + random.randint(-20, 20)
                    device.shell(f"input tap {tx} {ty}")
                    total_taps += 1
                    event_spell_count += 1
                    time.sleep(0.15)
                    
                    if total_taps >= EVENT_SPELL_MAX_TAPS:
                        break
                print(f"   🎪 {spell_file} → {total_taps}x taps")
        
        # Deploy normal spells (dengan interrupt ability)
        if spell_slot_indices:
            for idx, si in enumerate(spell_slot_indices):   # tambahkan enumerate
                slot_x = START_X + (si * GAP_X) + (GAP_X // 2)
                device.shell(f"input tap {slot_x} {TAP_Y}")
                time.sleep(0.2)
                
                if idx % 2 == 0:
                    coords = SPELL_COORDS_2
                    tipe = "3x"
                else:
                    coords = SPELL_COORDS_1
                    tipe = "5x"
                
                for cx, cy in coords:
                    tx = cx + random.randint(-15, 15)
                    ty = cy + random.randint(-15, 15)
                    device.shell(f"input tap {tx} {ty}")
                    normal_spell_count += 1
                    time.sleep(0.2)
                    
                    # Cek ability setiap tap
                    elapsed = time.time() - start_time
                    for idx2, (slot_x2, delay2) in enumerate(hero_deploy_info):
                        if not ability_activated[idx2] and elapsed >= delay2:
                            device.shell(f"input tap {slot_x2} {TAP_Y}")
                            print(f"   ⚡ Hero ability! (x={slot_x2})")
                            ability_activated[idx2] = True
                
                print(f"   🔮 Spell slot {si} → {len(coords)}x [{tipe}]")
        
        # ── Setelah semua spell selesai, aktifkan ability yang belum aktif ──
        elapsed_total = time.time() - start_time
        if elapsed_total < max_delay:
            print(f"   ⏳ Sisa delay {max_delay - elapsed_total:.1f}s...")
            time.sleep(max_delay - elapsed_total)
        
        # Aktifkan semua hero yang belum aktif (jika ada)
        for idx, (slot_x, delay) in enumerate(hero_deploy_info):
            if not ability_activated[idx]:
                device.shell(f"input tap {slot_x} {TAP_Y}")
                print(f"   ⚡ Hero ability! (x={slot_x})")
                ability_activated[idx] = True
        
        print(f"   📊 Total: {deployed_count} troop | {event_troop_count} event troop | {event_spell_count} event spell | {normal_spell_count} spell")
        
    else:
        # ── Kasus tanpa hero ──
        print(f"   🔮 Deploy spells...")
        event_spell_count = deploy_event_spells()
        normal_spell_count = deploy_spells_by_slots(spell_slot_indices)
        print(f"   📊 Total: {deployed_count} troop | {event_troop_count} event troop | {event_spell_count} event spell | {normal_spell_count} spell")

# ╔══════════════════════════════════════════════════════════════╗
# ║              BATTLE SEQUENCE                                ║
# ╚══════════════════════════════════════════════════════════════╝
def wait_for_match_found(timeout=60):
    """Tunggu match ditemukan. Return: 'found', 'connection_lost', atau 'timeout'"""
    start = time.time()
    last_print = 0

    while True:
        elapsed = time.time() - start

        # Timeout = kemungkinan internet masalah
        if elapsed > timeout:
            save_debug_screenshot("searching_timeout")
            print(f"   ⏱️ Search timeout {timeout}s! Internet kemungkinan bermasalah.")
            return "timeout"

        # Cek connection lost
        if handle_connection_lost():
            print("   ⚠️ Connection lost saat searching!")
            return "connection_lost"

        # Cek attack setup = musuh ketemu
        if find_template("attack_setup.png"):
            print(f"   ✅ Match found! ({int(elapsed)}s)")
            return "found"

        # Status setiap 10 detik
        if elapsed - last_print >= 10:
            searching = find_template(TEMPLATE_SEARCHING, threshold=0.80)
            if searching:
                print(f"   ⏳ Still searching... {int(elapsed)}s/{timeout}s")
            else:
                print(f"   ⏳ Waiting... {int(elapsed)}s/{timeout}s")
            last_print = elapsed

        time.sleep(1)
        
def force_restart_coc():
    """Force close dan restart Clash of Clans untuk reset koneksi yang macet."""
    print("   🔄 Force restart CoC untuk reset koneksi...")
    try:
        # 1. Paksa tutup aplikasi
        device.shell("am force-stop com.supercell.clashofclans")
        time.sleep(2)
        
        # 2. Buka lagi
        device.shell("am start -n com.supercell.clashofclans/.GameApp")
        print("   ⏳ Menunggu loading ulang...")
        time.sleep(8)  # Kasih waktu loading
        
        # 3. Bersihkan popup setelah masuk
        clear_popups_and_recover()
        print("   ✅ CoC berhasil di-restart!")
        return True
    except Exception as e:
        print(f"   ⚠️ Gagal restart CoC: {e}")
        return False   
         
def battle_sequence(army_loaded=False):
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

                if not army_loaded:
                    load_saved_army()
                    army_loaded = True

                print("⏳ Menunggu match...")
                match_result = wait_for_match_found(timeout=SEARCHING_TIMEOUT)

                if match_result == "timeout":
                    print("   ⏱️ Searching timeout! Koneksi kemungkinan macet.")
                    force_restart_coc()  # <-- RESTART COC
                    return army_loaded
                elif match_result == "connection_lost":
                    return army_loaded
                # match_result == "found" → lanjut ke bawah

                print("⚙️ Konfirmasi Army...")
                find_and_click("attack_setup.png")

                # ── FASE LOADING AWAN BERBASIS DETEKSI searching_opponents.png ──
                print("⏳ Memuat pertempuran (deteksi searching_opponents)...")
                start_load = time.time()
                pernah_ketemu_search = False
                battle_loaded = False

                while time.time() - start_load < SEARCHING_TIMEOUT:  # 60 detik
                    if handle_connection_lost():
                        print("   ⚠️ Connection lost saat loading!")
                        return army_loaded

                    # Cek apakah layar "Searching" masih muncul
                    if find_template(TEMPLATE_SEARCHING, threshold=0.80):
                        if not pernah_ketemu_search:
                            pernah_ketemu_search = True
                            print("   🔍 Searching opponents detected... menunggu hilang")
                        # Masih searching, lanjut tunggu
                        time.sleep(0.5)
                        continue

                    # Jika searching hilang:
                    if pernah_ketemu_search:
                        # Barusan selesai searching → langsung masuk battle
                        print("   ✅ Searching hilang → battle loaded!")
                        battle_loaded = True
                        break

                    # Jika searching tidak pernah muncul sama sekali:
                    # Cek apakah layar attack_setup sudah hilang (artinya sudah masuk battle)
                    if not find_template("attack_setup.png", threshold=0.70):
                        print("   ✅ Battle loaded instantly (tanpa searching)!")
                        battle_loaded = True
                        break

                    # Belum ada perubahan, tunggu sebentar
                    time.sleep(0.3)

                # ── Timeout handling ──
                if not battle_loaded:
                    print(f"   ⏱️ Loading battle timeout {SEARCHING_TIMEOUT}s! Koneksi macet.")
                    save_debug_screenshot("loading_timeout")
                    force_restart_coc()
                    return army_loaded

                # Kasih jeda kecil biar UI stabil
                time.sleep(1.0)

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
                            return army_loaded

                if handle_connection_lost():
                    return army_loaded

                print("🏳️ Surrender!")
                device.shell("input tap 62 420")
                time.sleep(1.5)

                if handle_connection_lost():
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
                else:
                    print("❌ Find Match tidak ditemukan!")
                    save_debug_screenshot("no_find_match")
        else:
            if handle_connection_lost():
                print("   ⚠️ Ternyata connection lost!")
            else:
                print("❌ Attack button tidak ditemukan!")
                save_debug_screenshot("no_attack_btn")

    except Exception as e:
        print(f"❌ ERROR di battle: {e}")
        logger.error(f"Battle error: {e}")
        save_debug_screenshot("battle_error")

        if handle_connection_lost():
            return army_loaded

        print("🔧 Recovery...")
        for _ in range(3):
            device.shell("input keyevent 4")
            time.sleep(0.5)
        clear_popups_and_recover()
        time.sleep(2)

    return army_loaded

# ╔══════════════════════════════════════════════════════════════╗
# ║              TARGETED UPGRADE SYSTEM (v3)                   ║
# ╚══════════════════════════════════════════════════════════════╝

def is_in_menu(x, y):
    return MENU_LEFT <= x <= MENU_RIGHT and MENU_TOP <= y <= MENU_BOTTOM

def scroll_menu_down():
    device.shell(f"input swipe {SCROLL_X} {SCROLL_Y_BOTTOM} {SCROLL_X} {SCROLL_Y_TOP} {SCROLL_SPEED}")
    time.sleep(1.5)

def scan_buildings_in_menu(screen):
    """Scan menu untuk building, return sorted by priority."""
    found = []
    for tpl_file, label, is_hero, priority in BUILDING_TEMPLATES:
        pos = find_on_screen(tpl_file, screen, threshold=DETECT_THRESHOLD, scales=MULTI_SCALES)
        if pos is None:
            continue
        cx, cy, conf = pos
        if is_in_menu(cx, cy):
            found.append((label, cx, cy, conf, is_hero, priority))
    # Sort: priority 1 dulu, 2, 3... 0 = normal (terakhir)
    found.sort(key=lambda x: x[5] if x[5] > 0 else 999)
    return found

def scan_lab_in_menu(screen):
    """Scan menu lab untuk research items, return sorted by priority."""
    found = []
    for tpl_file, label, priority in LAB_TEMPLATES:
        pos = find_on_screen(tpl_file, screen, threshold=DETECT_THRESHOLD, scales=MULTI_SCALES)
        if pos is None:
            continue
        cx, cy, conf = pos
        found.append((label, cx, cy, conf, priority))
    found.sort(key=lambda x: x[4] if x[4] > 0 else 999)
    return found


def find_upgrade_button_on_screen(screen, threshold=UPGRADE_THRESHOLD):
    best = None

    dim = find_on_screen(TEMPLATE_UPGRADE, screen, threshold, scales=MULTI_SCALES)
    if dim:
        best = dim

    bold = find_on_screen(TEMPLATE_UPGRADE_BOLD, screen, threshold, scales=MULTI_SCALES)
    if bold:
        if best is None or bold[2] > best[2]:
            best = bold

    if best:
        ver = "bold" if (bold is not None and best == bold) else "dim"
        print(f"   🔘 Upgrade btn [{ver}]: ({best[0]}, {best[1]}) conf={best[2]:.2f}")
    return best

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-UPGRADE BUILDING (TARGETED v3)            ║
# ╚══════════════════════════════════════════════════════════════╝
def auto_upgrade_suggested_fallback(context="builder"):
    """Fallback: upgrade apapun yang CoC suggest. Return (upgraded, resource_limited)."""
    upgraded = 0
    resource_limited = False

    print(f"\n   📋 FASE 2: Suggested Upgrades (fallback, {context})...")

    screen = take_screenshot()
    header = find_on_screen(TEMPLATE_HEADER, screen, threshold=HEADER_THRESHOLD)
    if header is None:
        if context == "lab":
            device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
        else:
            device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
        time.sleep(DELAY_MENU_LOAD)

    for attempt in range(MAX_SCROLLS + 1):
        if handle_connection_lost():
            clear_popups_and_recover()
            break

        screen = take_screenshot()

        header = find_on_screen(TEMPLATE_HEADER, screen, threshold=HEADER_THRESHOLD)
        if header is None:
            if attempt > 0:
                break
            continue

        hx, hy, hconf = header

        # Klik di (header_x, header_y + 28)
        tap(hx, hy + 28)
        print(f"   🎯 Suggested: klik item ({hx}, {hy + 28}) header_conf={hconf:.2f}")
        time.sleep(DELAY_AFTER_TAP)

        if context == "builder":
            # BUILDER: cari upgrade button → confirm
            btn_screen = take_screenshot()

            if find_on_screen(TEMPLATE_BUSY, btn_screen, threshold=BUSY_THRESHOLD):
                print(f"   🔴 Builders busy (suggested)")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                break

            upgrade = find_upgrade_button_on_screen(btn_screen, threshold=UPGRADE_THRESHOLD)
            if upgrade is None:
                print(f"   ⚠️ Suggested: Upgrade button tidak ditemukan → resource kurang atau bukan building")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                resource_limited = True
                continue

            tap(upgrade[0], upgrade[1])
            time.sleep(DELAY_AFTER_TAP)

            confirm_screen = take_screenshot()
            confirm = find_confirm_button_on_screen(confirm_screen, context="all")
            if not confirm:
                print(f"   ⚠️ Suggested: Semua confirm gagal → resource kurang!")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                resource_limited = True
                continue

            tap(confirm[0], confirm[1])
            time.sleep(DELAY_AFTER_TAP)

        else:
            # LAB: langsung confirm (TANPA upgrade button)
            confirm_screen = take_screenshot()
            confirm = find_confirm_button_on_screen(confirm_screen, context="lab")
            if not confirm:
                print(f"   ⚠️ Suggested (lab): Confirm tidak ditemukan → resource kurang!")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                resource_limited = True
                continue

            tap(confirm[0], confirm[1])
            time.sleep(DELAY_AFTER_TAP)

        # Post-confirm checks
        post_screen = take_screenshot()

        if find_on_screen(TEMPLATE_BUSY, post_screen, threshold=BUSY_THRESHOLD):
            print(f"   🔴 Builders busy (suggested, setelah confirm)")
            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            break

        if find_on_screen(TEMPLATE_HEY_CHIEF, post_screen, threshold=HEY_CHIEF_THRESHOLD):
            print(f"   🔴 Hey Chief! (suggested, setelah confirm)")
            for _ in range(3):
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(0.8)
            break

        upgraded += 1
        print(f"   ✅ Suggested upgrade #{upgraded}")

        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        if context == "lab":
            device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
        else:
            device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
        time.sleep(DELAY_MENU_LOAD)

    tap(CLOSE_X, CLOSE_Y)
    time.sleep(DELAY_AFTER_CLOSE)
    clear_popups_and_recover()

    print(f"   📊 Suggested fallback ({context}): {upgraded} up | resource_limit={resource_limited}")
    return upgraded, resource_limited

def auto_upgrade_building():
    print("\n🏠 ════════════════════════════════════════")
    print("   AUTO-UPGRADE: BUILDING (TARGETED) [OPTIMIZED]")
    print("   ════════════════════════════════════════")

    upgraded = 0
    skipped = 0
    already_upgrading = 0
    resource_limited = False
    completed_labels = set()
    skipped_resource = set()
    stop_reason = ""

    device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
    time.sleep(DELAY_MENU_LOAD)

    for scroll_idx in range(MAX_SCROLLS + 1):
        if handle_connection_lost():
            clear_popups_and_recover()
            break

        screen = take_screenshot()

        header = find_on_screen(TEMPLATE_HEADER, screen, threshold=HEADER_THRESHOLD)
        if header is None and scroll_idx > 0:
            stop_reason = "Menu hilang"
            break

        buildings = scan_buildings_in_menu(screen)
        new = [b for b in buildings if b[0] not in completed_labels and b[0] not in skipped_resource]

        if not new:
            scroll_menu_down()
            continue

        label, bx, by, bconf, is_hero, priority = new[0]
        print(f"   🏠 {label} (conf={bconf:.2f}, pri={priority})")

        tap(bx, by)
        time.sleep(DELAY_AFTER_TAP)

        # ════════════════════════════════════════════
        # SATU SCREENSHOT untuk semua cek
        # ════════════════════════════════════════════
        check_screen = take_screenshot()

        # ── HERO PATH ──
        if is_hero:
            confirm = find_confirm_button_on_screen(check_screen, context="hero")
            if not confirm:
                # Cek finish now (lagi di-upgrade)
                if find_on_screen(TEMPLATE_FINISH_NOW, check_screen, threshold=FINISH_NOW_THRESHOLD):
                    print(f"   ⏸️ {label}: Lagi di-upgrade (Finish Now)")
                    tap(CLOSE_X, CLOSE_Y)
                    time.sleep(DELAY_AFTER_CLOSE)
                    already_upgrading += 1
                    completed_labels.add(label)
                    device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
                    time.sleep(DELAY_MENU_LOAD)
                    continue

                # Cek builder busy
                if find_on_screen(TEMPLATE_BUSY, check_screen, threshold=BUSY_THRESHOLD):
                    print(f"   🔴 All builders busy! (hero confirm gagal)")
                    tap(CLOSE_X, CLOSE_Y)
                    time.sleep(DELAY_AFTER_CLOSE)
                    stop_reason = "Builders busy"
                    break

        # 🔥 PERBAIKAN DI SINI:
                # Jika confirm hilang, dan bukan karena busy/finish_now, artinya RESOURCE KURANG
                print(f"   ⚠️ {label}: Confirm hero tidak ditemukan → resource kurang atau max!")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                skipped += 1
                completed_labels.add(label)
                resource_limited = True          # <--- TAMBAHKAN INI
                skipped_resource.add(label)      # <--- TAMBAHKAN INI (biar ga diulang terus)
                device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
                time.sleep(DELAY_MENU_LOAD)
                # JANGAN break, tapi kita lanjut ke item berikutnya.
                # Tapi karena resource_limited sudah True, setelah fungsi selesai, main loop akan tau untuk farm lagi.
                continue

            ccx, ccy, cconf = confirm
            tap(ccx, ccy)
            time.sleep(DELAY_AFTER_TAP)

            # Cek hasil confirm - SATU SCREENSHOT
            post_screen = take_screenshot()

            if find_on_screen(TEMPLATE_BUSY, post_screen, threshold=BUSY_THRESHOLD):
                print(f"   🔴 All builders busy! (hero, setelah confirm)")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                stop_reason = "Builders busy"
                break

            if find_on_screen(TEMPLATE_FINISH_NOW, post_screen, threshold=FINISH_NOW_THRESHOLD):
                print(f"   ✅ {label} UPGRADED & VERIFIED!")
            else:
                print(f"   ✅ {label} UPGRADED (verification uncertain)")

            upgraded += 1
            completed_labels.add(label)
            logger.info(f"Hero upgraded: {label}")

            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
            time.sleep(DELAY_MENU_LOAD)
            continue

        # ── BUILDING PATH ──
        # Semua cek pakai check_screen yang sama
        has_upgrade = find_upgrade_button_on_screen(check_screen, threshold=UPGRADE_THRESHOLD)
        has_cancel_dim = find_on_screen(TEMPLATE_CANCEL_DIM, check_screen, threshold=CANCEL_THRESHOLD)
        has_cancel_bold = find_on_screen(TEMPLATE_CANCEL_BOLD, check_screen, threshold=CANCEL_THRESHOLD)

        if has_upgrade:
            # Cek busy di screenshot yang sama
            if find_on_screen(TEMPLATE_BUSY, check_screen, threshold=BUSY_THRESHOLD):
                print(f"   🔴 All builders busy!")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                stop_reason = "Builders busy"
                break

            ux, uy, uconf = has_upgrade
            tap(ux, uy)
            time.sleep(DELAY_AFTER_TAP)

            confirm_screen = take_screenshot()
            confirm = find_confirm_button_on_screen(confirm_screen, context="building")

            if not confirm:
                print(f"   ⚠️ {label}: Semua confirm gagal → resource kurang!")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                resource_limited = True
                skipped_resource.add(label)
                device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
                time.sleep(DELAY_MENU_LOAD)
                continue

            ccx, ccy, cconf = confirm
            tap(ccx, ccy)
            time.sleep(DELAY_AFTER_TAP)

            # Post-confirm: SATU SCREENSHOT
            post_screen = take_screenshot()

            if find_on_screen(TEMPLATE_BUSY, post_screen, threshold=BUSY_THRESHOLD):
                print(f"   🔴 All builders busy! (setelah confirm)")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                stop_reason = "Builders busy"
                break

            if find_on_screen(TEMPLATE_HEY_CHIEF, post_screen, threshold=HEY_CHIEF_THRESHOLD):
                print(f"   🔴 Hey Chief! (setelah confirm)")
                for _ in range(3):
                    tap(CLOSE_X, CLOSE_Y)
                    time.sleep(0.8)
                stop_reason = "Builders busy (Hey Chief)"
                break

            # Verifikasi di screenshot yang sama
            verified = False
            if find_on_screen(TEMPLATE_CANCEL_DIM, post_screen, threshold=CANCEL_THRESHOLD):
                verified = True
            elif find_on_screen(TEMPLATE_CANCEL_BOLD, post_screen, threshold=CANCEL_THRESHOLD):
                verified = True

            if verified:
                print(f"   ✅ {label} UPGRADED & VERIFIED!")
            else:
                print(f"   ✅ {label} UPGRADED (verification uncertain)")

            upgraded += 1
            completed_labels.add(label)
            logger.info(f"Building upgraded: {label}")

            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
            time.sleep(DELAY_MENU_LOAD)
            continue

        else:
            if has_cancel_dim or has_cancel_bold:
                print(f"   ⏸️ {label}: Lagi di-upgrade")
                tap(CLOSE_X, CLOSE_Y)
                time.sleep(DELAY_AFTER_CLOSE)
                already_upgrading += 1
                completed_labels.add(label)
                device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
                time.sleep(DELAY_MENU_LOAD)
                continue

            print(f"   ⏭️ {label}: Tidak bisa di-upgrade")
            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            skipped += 1
            completed_labels.add(label)
            device.shell(f"input tap {BUILDER_HEAD_X} {BUILDER_HEAD_Y}")
            time.sleep(DELAY_MENU_LOAD)
            continue

    tap(CLOSE_X, CLOSE_Y)
    time.sleep(DELAY_AFTER_CLOSE)

    print(f"   📊 Targeted: {upgraded} up | {skipped} skip | {already_upgrading} already | resource_limit={resource_limited} | {stop_reason or 'done'}")

    # FASE 2: Fallback
    if ENABLE_FALLBACK_TO_SUGGESTED and stop_reason != "Builders busy" and stop_reason != "Builders busy (Hey Chief)":
        s_up, s_limited = auto_upgrade_suggested_fallback(context="builder")
        upgraded += s_up
        if s_limited:
            resource_limited = True

    print(f"   📊 Total building: {upgraded} up | resource_limit={resource_limited}")
    logger.info(f"Building upgrade: {upgraded} up, resource_limit={resource_limited}")
    return upgraded, resource_limited

# ╔══════════════════════════════════════════════════════════════╗
# ║              AUTO-UPGRADE LAB (TARGETED v3)                 ║
# ╚══════════════════════════════════════════════════════════════╝
def auto_upgrade_lab():
    print("\n🔬 ════════════════════════════════════════")
    print("   AUTO-UPGRADE: LAB (TARGETED) [OPTIMIZED]")
    print("   ════════════════════════════════════════")

    upgraded = 0
    skipped = 0
    resource_limited = False
    completed_labels = set()
    skipped_resource = set()
    stop_reason = ""

    if not LAB_TEMPLATES:
        print("   ⏭️ LAB_TEMPLATES kosong!")
        if ENABLE_FALLBACK_TO_SUGGESTED:
            print("   📋 Buka Lab dulu, lalu fallback ke suggested upgrades...")
            device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
            time.sleep(DELAY_MENU_LOAD)
            s_up, s_limited = auto_upgrade_suggested_fallback(context="lab")
            upgraded += s_up
            if s_limited:
                resource_limited = True
        print(f"   📊 Lab: {upgraded} up (fallback) | resource_limit={resource_limited}")
        logger.info(f"Lab: {upgraded} up (fallback)")
        return upgraded, resource_limited

    device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
    time.sleep(DELAY_MENU_LOAD)

    # Cek lab busy - SATU SCREENSHOT
    init_screen = take_screenshot()
    if find_on_screen(TEMPLATE_UPGRADE_IN_PROGRESS, init_screen, threshold=UIP_THRESHOLD):
        print(f"   ⏸️ Lab lagi research (Upgrade in Progress)! Skip.")
        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        return 0, False

    for scroll_idx in range(MAX_SCROLLS + 1):
        if handle_connection_lost():
            clear_popups_and_recover()
            break

        screen = take_screenshot()

        items = scan_lab_in_menu(screen)
        new = [i for i in items if i[0] not in completed_labels and i[0] not in skipped_resource]

        if not new:
            scroll_menu_down()
            continue

        label, ix, iy, iconf, priority = new[0]
        print(f"   🔬 {label} (conf={iconf:.2f}, pri={priority})")

        tap(ix, iy)
        time.sleep(DELAY_AFTER_TAP)

        # SATU SCREENSHOT untuk semua cek
        check_screen = take_screenshot()

        if find_on_screen(TEMPLATE_UPGRADE_IN_PROGRESS, check_screen, threshold=UIP_THRESHOLD):
            print(f"   ⏸️ {label}: Lagi di-upgrade!")
            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            completed_labels.add(label)
            device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
            time.sleep(DELAY_MENU_LOAD)
            continue

        if find_on_screen(TEMPLATE_LAB_BUSY, check_screen, threshold=BUSY_THRESHOLD):
            print(f"   🔴 Lab sedang research!")
            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            stop_reason = "Lab busy"
            break

        confirm = find_confirm_button_on_screen(check_screen, context="lab")
        if not confirm:
            print(f"   ⚠️ {label}: Semua confirm gagal → resource kurang!")
            tap(CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            resource_limited = True
            skipped_resource.add(label)
            device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
            time.sleep(DELAY_MENU_LOAD)
            continue

        ccx, ccy, cconf = confirm
        tap(ccx, ccy)
        time.sleep(DELAY_AFTER_TAP)

        # Post-confirm: SATU SCREENSHOT
        post_screen = take_screenshot()
        if find_on_screen(TEMPLATE_UPGRADE_IN_PROGRESS, post_screen, threshold=UIP_THRESHOLD):
            print(f"   ✅ {label} UPGRADED & VERIFIED!")
        else:
            print(f"   ✅ {label} UPGRADED (verification uncertain)")

        upgraded += 1
        completed_labels.add(label)
        logger.info(f"Lab upgraded: {label}")

        tap(CLOSE_X, CLOSE_Y)
        time.sleep(DELAY_AFTER_CLOSE)
        clear_popups_and_recover()
        device.shell(f"input tap {LAB_ICON_X} {LAB_ICON_Y}")
        time.sleep(DELAY_MENU_LOAD)

        # Cek lab mulai research
        verify_screen = take_screenshot()
        if find_on_screen(TEMPLATE_UPGRADE_IN_PROGRESS, verify_screen, threshold=UIP_THRESHOLD):
            print(f"   ✅ Lab confirmed researching!")
            break

    tap(CLOSE_X, CLOSE_Y)
    time.sleep(DELAY_AFTER_CLOSE)

    print(f"   📊 Lab targeted: {upgraded} up | {skipped} skip | resource_limit={resource_limited} | {stop_reason or 'done'}")

    if ENABLE_FALLBACK_TO_SUGGESTED and stop_reason != "Lab busy":
        if skipped > 0 or upgraded == 0:
            print(f"   📋 Lab fallback ke suggested upgrades...")
            s_up, s_limited = auto_upgrade_suggested_fallback(context="lab")
            upgraded += s_up
            if s_limited:
                resource_limited = True
                
    clear_popups_and_recover()
    
    print(f"   📊 Lab total: {upgraded} up | resource_limit={resource_limited}")
    logger.info(f"Lab upgrade: {upgraded} up, resource_limit={resource_limited}")
    return upgraded, resource_limited

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
    print("   BOT FARM + AUTO-UPGRADE v3 (TARGETED)")
    print("=" * 55)
    print(f"    Total akun    : {len(DAFTAR_AKUN)}")
    print(f"   ▶️  Mulai dari    : Index {INDEX_AKUN_MULAI} ({DAFTAR_AKUN[INDEX_AKUN_MULAI][1]})")

    stop_str = f"Index {STOP_AFTER_INDEX} ({DAFTAR_AKUN[STOP_AFTER_INDEX][1]})" if 0 <= STOP_AFTER_INDEX < len(DAFTAR_AKUN) else "Akhir Daftar"
    print(f"   🛑 Stop di       : {stop_str}")
    print(f"    Looping       : {'Ya' if LOOP_CONTINUOUSLY else 'Tidak'}")
    print(f"   🏠 Upgrade Bldg  : {'AKTIF' if ENABLE_UPGRADE_BUILDING else 'MATI'}")
    print(f"   🔬 Upgrade Lab   : {'AKTIF' if ENABLE_UPGRADE_LAB else 'MATI'}")
    print(f"   🔄 Max Siklus    : {MAX_FARM_UPGRADE_CYCLES}")
    print("=" * 55)
    logger.info("Bot Farm+Auto v3 started")

    # ── CEK PROGRESS TERAKHIR ──
    resume_idx, resume_name = load_progress()
    if resume_idx is not None:
        print(f"\n   📂 Ditemukan progress terakhir: {resume_name} (index {resume_idx})")
        print(f"   🕐 Disimpan: dari sesi sebelumnya")
        print(f"\n   Pilihan:")
        print(f"   [1] Lanjut dari {resume_name} (index {resume_idx})")
        print(f"   [2] Mulai dari awal (index {INDEX_AKUN_MULAI})")

        # Non-interactive: otomatis lanjut dari progress
        # Kalau mau manual, uncomment bagian input di bawah
        # try:
        #     pilihan = input("   Pilih (1/2): ").strip()
        # except:
        #     pilihan = "1"
        # current_index = resume_idx if pilihan == "1" else INDEX_AKUN_MULAI

        # Otomatis lanjut
        current_index = resume_idx
        print(f"   ✅ Melanjutkan dari {resume_name} (index {current_index})")
        is_first_run = False
    else:
        current_index = INDEX_AKUN_MULAI
        is_first_run = True

    config = load_config()

    # ── SWITCH KE AKUN AWAL (hanya kalau fresh start) ──
    if is_first_run and len(DAFTAR_AKUN) > 1:
        scid_awal, nama_awal = DAFTAR_AKUN[current_index]
        print(f"\n🔄 Switch ke akun awal: {nama_awal} (Index {current_index})")

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

    while True:
        while current_index < total_akun:

            if STOP_AFTER_INDEX != -1 and current_index > STOP_AFTER_INDEX:
                print(f"🛑 Batas akun tercapai (Index {STOP_AFTER_INDEX}).")
                break

            scid_file, nama = DAFTAR_AKUN[current_index]

            # ── BACA STATE AKUN ──
            state = get_account_state(scid_file)
            if state:
                battle_count_akun = state.get("battle_count", 0)
                upgrade_count_akun = state.get("upgrade_count", 0)
                cycle_awal = state.get("cycle", 0)
                print(f"   📊 State: battle={battle_count_akun}, upgrade={upgrade_count_akun}, cycle={cycle_awal}")
            else:
                battle_count_akun = 0
                upgrade_count_akun = 0
                cycle_awal = 0
                update_account_state(scid_file, battle_count=0, upgrade_count=0, cycle=0)

            # ── SIMPAN PROGRESS POSISI ──
            save_progress(current_index, nama)

            print()
            print("" + "─" * 53 + "┐")
            print(f"│  AKUN : {nama.upper():<20} [Index {current_index}, {current_index + 1}/{total_akun}]")
            print(f"│  SCID : {scid_file}")
            print("└" + "─" * 53 + "")
            logger.info(f"=== AKUN: {nama} ({current_index}/{total_akun}) ===")

            # ── SWITCH AKUN (hanya jika bukan first run dan multi account) ──
            if not is_first_run and len(DAFTAR_AKUN) > 1:
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

            # ── ZOOM ──
            # Pastikan CoC running sebelum mulai
            if not ensure_coc_running():
                print(f"   ❌ CoC gagal! Skip akun {nama}...")
                current_index += 1
                continue
            try:
                zoom_ctrl.zoom_out()
            except Exception as e:
                print(f"   ⚠️ Zoom error: {e}, lanjut tanpa zoom")
                logger.error(f"Zoom error: {e}")
                save_debug_screenshot("zoom_error")
            time.sleep(1)

            # ── DETEKSI DE ──
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

            # ═══════════════════════════════════════════════════════
            # SIKLUS: FARM → UPGRADE (mulai dari cycle_awal)
            # ═══════════════════════════════════════════════════════
            for cycle in range(cycle_awal, MAX_FARM_UPGRADE_CYCLES):
                print(f"\n   🔄 ══ SIKLUS #{cycle + 1}/{MAX_FARM_UPGRADE_CYCLES} ══")

                gold_full, elixir_full, de_full = cek_status_resource(punya_de)
                print(format_resource_status(gold_full, elixir_full, de_full, punya_de))

                # ── FARMING ──
                if not is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                    print(f"\n   🌾 Storage belum penuh → FARMING...")
                    start_sesi = time.time()
                    battle_local = 0
                    army_loaded = False

                    while True:
                        army_loaded = battle_sequence(army_loaded=army_loaded)
                        battle_local += 1
                        battle_count_akun += 1
                        total_battle_semua += 1
                        print(f"\n   ⚔️ Battle #{battle_local} [{nama}] selesai (total akun={battle_count_akun})")
                        logger.info(f"Battle #{battle_local} [{nama}] selesai")

                        # Update state setiap battle (bisa juga setiap 5 battle untuk efisiensi)
                        update_account_state(scid_file, battle_count=battle_count_akun, upgrade_count=upgrade_count_akun, cycle=cycle)

                        time.sleep(2)
                        handle_connection_lost()
                        clear_popups_and_recover()
                        time.sleep(1)

                        gold_full, elixir_full, de_full = cek_status_resource(punya_de)
                        print(format_resource_status(gold_full, elixir_full, de_full, punya_de))

                        if is_storage_penuh(gold_full, elixir_full, de_full, punya_de):
                            print(f"   ✅ Storage PENUH setelah {battle_local} battle!")
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
                    print(f"\n   ⚠️ Storage sudah PENUH → langsung upgrade")

                # ── UPGRADE ──
                cycle_upgrades = 0
                any_resource_limited = False

                if ENABLE_UPGRADE_BUILDING or ENABLE_UPGRADE_LAB:
                    print(f"\n   🔧 Memulai auto-upgrade...")
                    clear_popups_and_recover()
                    time.sleep(1)

                    if ENABLE_UPGRADE_BUILDING:
                        b_up, b_limited = auto_upgrade_building()
                        cycle_upgrades += b_up
                        upgrade_count_akun += b_up
                        total_upgrade_semua += b_up
                        if b_limited:
                            any_resource_limited = True
                    else:
                        print("   ⏭️ Building upgrade: SKIP (mati)")

                    device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
                    time.sleep(DELAY_AFTER_CLOSE)

                    if ENABLE_UPGRADE_LAB:
                        l_up, l_limited = auto_upgrade_lab()
                        cycle_upgrades += l_up
                        upgrade_count_akun += l_up
                        total_upgrade_semua += l_up
                        if l_limited:
                            any_resource_limited = True
                    else:
                        print("   ⏭️ Lab upgrade: SKIP (mati)")

                    device.shell(f"input tap {CLOSE_X} {CLOSE_Y}")
                    time.sleep(DELAY_AFTER_CLOSE)
                    clear_popups_and_recover()

                    print(f"   📊 Siklus #{cycle + 1}: {cycle_upgrades} upgrade")
                    # Update state setelah upgrade
                    update_account_state(scid_file, battle_count=battle_count_akun, upgrade_count=upgrade_count_akun, cycle=cycle)

                # ── KEPUTUSAN LANJUT / BERHENTI ──
                if cycle_upgrades == 0 and not any_resource_limited:
                    print(f"   ℹ️ Ga ada upgrade & resource OK → selesai")
                    break

                if not any_resource_limited and cycle_upgrades > 0:
                    print(f"   ℹ️ Upgrade berhasil, resource masih ada → coba lagi")
                    continue

                if any_resource_limited:
                    if cycle < MAX_FARM_UPGRADE_CYCLES - 1:
                        print(f"   🔃 Resource kurang → farm lagi")
                    else:
                        print(f"   ⏱️ Batas siklus ({MAX_FARM_UPGRADE_CYCLES})")

            # AKHIR SESI AKUN
            print(f"   ✅ Akun {nama} selesai!")
            current_index += 1

        # AKHIR INNER LOOP (semua akun selesai)
        if not LOOP_CONTINUOUSLY:
            print(" Looping dimatikan. Bot berhenti.")
            clear_progress()
            break

        print(" Mengulang dari akun awal...")
        clear_progress()
        current_index = 0
        is_first_run = False
        time.sleep(5)

    # LAPORAN AKHIR
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

    press_home()
    time.sleep(1)
    close_ldplayer()
    print("   🖥️ LDPlayer minimized. Bye!")

if __name__ == "__main__":
    main_farming_loop()