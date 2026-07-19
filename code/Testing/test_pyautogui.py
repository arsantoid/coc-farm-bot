# ==========================================
# TEST PYAUTOGUI — Quick Window + Shift+X
# Jalankan: python test_pyautogui.py
# ==========================================
import pyautogui
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
            hasil.append((hwnd, buf.value))
    return True
user32.EnumWindows(ENUMPROC(callback), 0)

if not hasil:
    print("❌ LDPlayer tidak ditemukan!")
    exit()

hwnd, title = hasil[0]
print(f"✅ LDPlayer: [{hwnd}] {title}")

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

# === Force Focus ke LDPlayer ===
tid_prev = user32.GetWindowThreadProcessId(hwnd_prev, None)
tid_target = user32.GetWindowThreadProcessId(hwnd, None)
user32.AttachThreadInput(tid_prev, tid_target, True)
user32.ShowWindow(hwnd, 9)
user32.BringWindowToTop(hwnd)
user32.SetForegroundWindow(hwnd)
user32.AttachThreadInput(tid_prev, tid_target, False)
time.sleep(0.3)

# === Kirim Shift+X via pyautogui ===
print("📤 Shift+X via pyautogui...")
pyautogui.hotkey('shift', 'x')
time.sleep(0.2)

# === Kembalikan ke window sebelumnya ===
user32.BringWindowToTop(hwnd_prev)
user32.SetForegroundWindow(hwnd_prev)
print(f"↩️ Kembali ke: {title_prev[:50]}")

print()
print("⏳ Tunggu 5 detik, lihat emulator...")
time.sleep(5)
print("SELESAI. Zoom out? (y/n)")