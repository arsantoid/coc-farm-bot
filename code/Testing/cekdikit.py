import os
import sys
import cv2
import numpy as np
from ppadb.client import Client as AdbClient

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR = os.path.join(BASE_DIR, "Gambar")
DEBUG_DIR  = os.path.join(BASE_DIR, "debug")
THRESHOLD  = 0.80

def main():
    template_path = os.path.join(GAMBAR_DIR, "lab_busy.png")
    if not os.path.exists(template_path):
        print(f"[ERROR] Template tidak ada: {template_path}")
        sys.exit(1)

    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    if not devices:
        print("[ERROR] Tidak ada device ADB.")
        sys.exit(1)
    device = devices[0]
    print(f"[ADB] Terhubung: {device.serial}")

    raw = device.screencap()
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    tmpl = cv2.imread(template_path, cv2.IMREAD_COLOR)

    result = cv2.matchTemplate(img, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    th, tw = tmpl.shape[:2]
    cx = max_loc[0] + tw // 2
    cy = max_loc[1] + th // 2
    found = max_val >= THRESHOLD

    print(f"\n  Template  : lab_busy.png")
    print(f"  Confidence: {max_val:.4f}")
    print(f"  Threshold : {THRESHOLD}")
    print(f"  Status    : {'DITEMUKAN' if found else 'TIDAK ditemukan'}")
    if found:
        print(f"  Posisi    : ({cx}, {cy})")

    # Simpan debug
    os.makedirs(DEBUG_DIR, exist_ok=True)
    dbg = img.copy()
    pt1 = max_loc
    pt2 = (max_loc[0] + tw, max_loc[1] + th)
    color = (0, 255, 0) if found else (0, 0, 255)
    cv2.rectangle(dbg, pt1, pt2, color, 2)
    cv2.putText(dbg, f"{max_val:.3f}", (pt1[0], pt1[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    import time
    path = os.path.join(DEBUG_DIR, f"test_lab_busy_{time.strftime('%Y%m%d_%H%M%S')}.png")
    cv2.imwrite(path, dbg)
    print(f"  Debug     : {path}")

if __name__ == "__main__":
    main()