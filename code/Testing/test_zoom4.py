# ==========================================
# ZOOM_BACKGROUND.py
# Kirim Ctrl+F9 ke LDPlayer TANPA focus window
# (pakai Windows PostMessage API)
# Jalankan: python zoom_background.py
# ==========================================

import ctypes
import time

user32 = ctypes.windll.user32

# Windows Message Constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_CONTROL = 0x11
VK_F9 = 0x78


def cari_window_ldplayer():
    """Cari semua window handle yang mengandung 'LDPlayer'."""
    hasil = []

    # Callback untuk EnumWindows
    ENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_int,
        ctypes.c_int
    )

    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if "ldplayer" in title.lower() and user32.IsWindowVisible(hwnd):
                hasil.append((hwnd, title))
        return True

    user32.EnumWindows(ENUMPROC(callback), 0)
    return hasil


def kirim_f9_background(hwnd):
    """Kirim Ctrl+F9 ke window tanpa mengubah focus.

    PostMessage = asynchronous, tidak butuh window focus.
    Pesan masuk ke message queue window target.
    """
    # Ctrl down
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, 0)
    time.sleep(0.02)
    # F9 down
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_F9, 0)
    time.sleep(0.02)
    # F9 up
    user32.PostMessageW(hwnd, WM_KEYUP, VK_F9, 0)
    time.sleep(0.02)
    # Ctrl up
    user32.PostMessageW(hwnd, WM_KEYUP, VK_CONTROL, 0)


def zoom_out_background(jumlah=6):
    """Zoom out LDPlayer dari background."""
    windows = cari_window_ldplayer()

    if not windows:
        print("❌ Window LDPlayer tidak ditemukan!")
        return False

    print(f"📋 Window ditemukan:")
    for hwnd, title in windows:
        print(f"   [{hwnd}] {title}")

    # Kirim ke window pertama yang ditemukan
    hwnd, title = windows[0]
    print(f"\n🔍 Mengirim Ctrl+F9 ke: {title}")
    print(f"   (Window lain tidak terganggu)\n")

    for i in range(jumlah):
        kirim_f9_background(hwnd)
        print(f"   Zoom out {i+1}/{jumlah}")
        time.sleep(0.3)

    print("\n✅ Zoom out selesai!")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("   ZOOM-OUT BACKGROUND (PostMessage)")
    print("=" * 50)
    print("   Kirim Ctrl+F9 tanpa ubah focus window")
    print("   YouTube/browsing tetap di depan")
    print("=" * 50)
    print("\nTekan ENTER untuk jalankan...")
    input()
    zoom_out_background()