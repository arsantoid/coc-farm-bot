# ==========================================
# ZOOM_MACRO.py
# Jalankan macro zoom out yang sudah direkam
# Jalankan: python zoom_macro.py
# ==========================================

import subprocess
import os
import time

# Path LDPlayer console (sesuaikan!)
LDCONSOLE = r"C:\LDPlayer\LDPlayer9\ldconsole.exe"

# Nama emulator (sesuaikan!)
EMULATOR_NAME = "MOSS"  # atau nama instance LDPlayer kamu


def jalankan_zoom_macro():
    """Jalankan macro zoom_out yang sudah direkam."""
    print("🔍 Menjalankan macro zoom out...")

    # Cara 1: Via ldconsole (jika support)
    cmd = f'"{LDCONSOLE}" operation-player --name "{EMULATOR_NAME}" --file zoom_out'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Macro zoom out berhasil dijalankan!")
    else:
        print(f"⚠️ ldconsole tidak support: {result.stderr}")
        print("   Jalankan macro manual dari toolbar LDPlayer")


if __name__ == "__main__":
    print("=" * 50)
    print("   ZOOM VIA LDMPLAYER MACRO")
    print("=" * 50)
    print("\nPastikan sudah rekam macro 'zoom_out' terlebih dahulu")
    print("Tekan ENTER untuk jalankan...")
    input()
    jalankan_zoom_macro()