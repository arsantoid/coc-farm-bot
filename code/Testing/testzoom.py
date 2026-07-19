# ==========================================
# TEST_FINAL_FIX.py (OPTIMASI)
# ==========================================
import subprocess
import tempfile
import os
import ctypes
import time

user32 = ctypes.windll.user32

# === Cari LDPlayer ===
hasil = []
ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
def callback(hwnd, _):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if "ldplayer" in buf.value.lower() and user32.IsWindowVisible(hwnd):
            hasil.append(hwnd)
    return True
user32.EnumWindows(ENUMPROC(callback), 0)

if not hasil:
    print("❌ LDPlayer tidak ditemukan!")
    exit()

hwnd_ld = hasil[0]
print(f"✅ LDPlayer: [{hwnd_ld}]")

# === Simpan window aktif ===
hwnd_prev = user32.GetForegroundWindow()
length = user32.GetWindowTextLengthW(hwnd_prev)
if length > 0:
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd_prev, buf, length + 1)
    title_prev = buf.value
else:
    title_prev = "Unknown"

print(f"📌 Window aktif: {title_prev[:50]}")

# === VBS: AppActivate + SendKeys ===
vbs = '''Set s = WScript.CreateObject("WScript.Shell")
s.AppActivate "LDPlayer"
WScript.Sleep 200
s.SendKeys "+z"'''

vbs_path = os.path.join(tempfile.gettempdir(), "zoom.vbs")
with open(vbs_path, "w") as f:
    f.write(vbs)

print("📤 VBS: AppActivate + Shift+Z...")
subprocess.run(["cscript", "//nologo", vbs_path],
                capture_output=True, timeout=10)
os.unlink(vbs_path)

# === TUNGGU (dari 1.5s → 0.5s) ===
time.sleep(0.5)

# === KEMBALIKAN WINDOW (re-attach) ===
hwnd_now = user32.GetForegroundWindow()
tid_now = user32.GetWindowThreadProcessId(hwnd_now, None)
tid_prev = user32.GetWindowThreadProcessId(hwnd_prev, None)

user32.AttachThreadInput(tid_now, tid_prev, True)
user32.BringWindowToTop(hwnd_prev)
user32.SetForegroundWindow(hwnd_prev)
user32.AttachThreadInput(tid_now, tid_prev, False)

print(f"↩️ Kembali ke: {title_prev[:50]}")

# === TUNGGU MACRO (dari 6s → 4.5s) ===
print("⏳ Tunggu macro (4.5 detik)...")
time.sleep(4.5)

# === SCROLL KE VIEW CERAH ===
from ppadb.client import Client as AdbClient
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()
device = devices[0]

print("📜 Scroll kamera ke view cerah...")
device.shell("input swipe 480 400 480 100 400")
time.sleep(1)
device.shell("input swipe 480 400 480 100 400")
time.sleep(1)

print("✅ SELESAI!")