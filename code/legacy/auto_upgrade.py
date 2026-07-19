import os
import sys
import time
import cv2
import numpy as np
from ppadb.client import Client as AdbClient


# ============================================================
#                     GLOBAL SETTINGS
# ============================================================

# --- Mode test ---
MODE = "full_flow"
# Pilihan: confirm_only | detect_header | detect_upgrade | check_busy
#          click_item | screenshot_only | full_flow

# --- Threshold template matching (0.0 - 1.0) ---
CONFIRM_THRESHOLD  = 0.80
HEADER_THRESHOLD   = 0.80
UPGRADE_THRESHOLD  = 0.80
BUSY_THRESHOLD     = 0.80

# --- Nama template (sesuai file di folder Gambar/) ---
TEMPLATE_CONFIRM   = "confirm_text.png"
TEMPLATE_HEADER    = "suggested_upgrades_text.png"
TEMPLATE_UPGRADE   = "upgrade_btn_dim.png"
TEMPLATE_BUSY      = "all_builders_busy.png"

# --- Koordinat Builder Head icon ---
BUILDER_HEAD_X = 450
BUILDER_HEAD_Y = 25

# --- Offset item pertama dari header (ke bawah) ---
ITEM_OFFSET_Y = 28

# --- Koordinat tutup dialog ---
CLOSE_X = 900
CLOSE_Y = 40

# --- Max loop (0 = unlimited) ---
MAX_LOOP = 0

# --- Delay (detik) ---
DELAY_AFTER_TAP   = 1.5
DELAY_AFTER_CLOSE = 1.0
DELAY_MENU_LOAD   = 3.0

# --- Path ---
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMBAR_DIR  = os.path.join(BASE_DIR, "Gambar")
DEBUG_DIR   = os.path.join(BASE_DIR, "debug")

# --- Debug ---
SAVE_DEBUG = True
VERBOSE    = True


# ============================================================
#                     KONEKSI ADB
# ============================================================

def connect_adb():
    print("[ADB] Menghubungkan ke emulator...")
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    if not devices:
        print("[ERROR] Tidak ada device terdeteksi! Pastikan LDPlayer jalan.")
        sys.exit(1)
    device = devices[0]
    print(f"[ADB] Terhubung: {device.serial}")
    return device


# ============================================================
#                   SCREENSHOT & DEBUG
# ============================================================

def take_screenshot(device):
    raw = device.screencap()
    img = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    return img


def save_debug_screenshot(img, name="debug"):
    if not SAVE_DEBUG:
        return None
    os.makedirs(DEBUG_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(DEBUG_DIR, f"{name}_{ts}.png")
    cv2.imwrite(path, img)
    if VERBOSE:
        print(f"[DEBUG] Screenshot: {path}")
    return path


# ============================================================
#                   TEMPLATE MATCHING
# ============================================================

def load_template(template_name):
    path = os.path.join(GAMBAR_DIR, template_name)
    if not os.path.exists(path):
        print(f"[ERROR] Template tidak ada: {path}")
        return None
    tmpl = cv2.imread(path, cv2.IMREAD_COLOR)
    if tmpl is None:
        print(f"[ERROR] Gagal baca: {path}")
    return tmpl


def find_template(device, template_name, threshold=0.80, region=None):
    """Cari satu match terbaik. Return: (found, cx, cy, confidence)"""
    screenshot = take_screenshot(device)
    if screenshot is None:
        return False, 0, 0, 0.0

    tmpl = load_template(template_name)
    if tmpl is None:
        return False, 0, 0, 0.0

    search_img = screenshot
    ox, oy = 0, 0
    if region:
        x1, y1, x2, y2 = region
        search_img = screenshot[y1:y2, x1:x2]
        ox, oy = x1, y1

    result = cv2.matchTemplate(search_img, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    th, tw = tmpl.shape[:2]
    cx = max_loc[0] + tw // 2 + ox
    cy = max_loc[1] + th // 2 + oy
    found = max_val >= threshold

    if VERBOSE:
        status = "DITEMUKAN" if found else "tidak ditemukan"
        print(f"[MATCH] {template_name}: {status} "
              f"(conf={max_val:.4f}, thresh={threshold}) -> ({cx}, {cy})")

    if SAVE_DEBUG:
        dbg = screenshot.copy()
        pt1 = (max_loc[0] + ox, max_loc[1] + oy)
        pt2 = (pt1[0] + tw, pt1[1] + th)
        color = (0, 255, 0) if found else (0, 0, 255)
        cv2.rectangle(dbg, pt1, pt2, color, 2)
        cv2.putText(dbg, f"{max_val:.3f}", (pt1[0], pt1[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        safe_name = template_name.replace(".png", "").replace(" ", "_")
        save_debug_screenshot(dbg, f"match_{safe_name}")

    return found, cx, cy, max_val


def find_all_matches(device, template_name, threshold=0.80, region=None):
    """Cari SEMUA lokasi template di layar. Return: list of (cx, cy, conf)"""
    screenshot = take_screenshot(device)
    if screenshot is None:
        return []

    tmpl = load_template(template_name)
    if tmpl is None:
        return []

    search_img = screenshot
    ox, oy = 0, 0
    if region:
        x1, y1, x2, y2 = region
        search_img = screenshot[y1:y2, x1:x2]
        ox, oy = x1, y1

    result = cv2.matchTemplate(search_img, tmpl, cv2.TM_CCOEFF_NORMED)
    th, tw = tmpl.shape[:2]

    locations = np.where(result >= threshold)
    matches = []
    seen = set()

    for pt_y, pt_x in zip(*locations):
        cx = pt_x + tw // 2 + ox
        cy = pt_y + th // 2 + oy
        conf = float(result[pt_y, pt_x])
        key = (cx // 30, cy // 30)
        if key not in seen:
            seen.add(key)
            matches.append((cx, cy, conf))

    matches.sort(key=lambda m: (m[1], m[0]))

    if VERBOSE:
        print(f"[MULTI] {template_name}: {len(matches)} match ditemukan")
        for i, (mx, my, mc) in enumerate(matches):
            print(f"        #{i+1}: ({mx}, {my}) conf={mc:.4f}")

    if SAVE_DEBUG and matches:
        dbg = screenshot.copy()
        for idx, (mx, my, mc) in enumerate(matches):
            tlx = mx - tw // 2
            tly = my - th // 2
            cv2.rectangle(dbg, (tlx, tly), (tlx + tw, tly + th), (0, 255, 0), 2)
            cv2.putText(dbg, f"#{idx+1} {mc:.3f}", (tlx, tly - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        safe_name = template_name.replace(".png", "").replace(" ", "_")
        save_debug_screenshot(dbg, f"all_{safe_name}")

    return matches


# ============================================================
#                      TAP / CLICK
# ============================================================

def tap(device, x, y):
    if VERBOSE:
        print(f"[TAP] ({x}, {y})")
    device.input_tap(x, y)


def find_and_click(device, template_name, threshold=0.80, region=None):
    found, cx, cy, conf = find_template(device, template_name, threshold, region)
    if found:
        tap(device, cx, cy)
        return True
    return False


# ============================================================
#             MODE: CLICK ITEM (test offset)
# ============================================================

def test_click_item(device):
    """Test klik item pertama di list. Menu harus sudah terbuka!"""
    print("\n" + "=" * 60)
    print("  MODE: CLICK ITEM (test offset)")
    print("  Menu Suggested upgrades harus sudah terbuka!")
    print("=" * 60 + "\n")

    found, hdr_cx, hdr_cy, conf = find_template(
        device, TEMPLATE_HEADER, HEADER_THRESHOLD
    )
    if not found:
        print("[GAGAL] Header tidak ditemukan!")
        return

    item_x = hdr_cx
    item_y = hdr_cy + ITEM_OFFSET_Y

    print(f"[OK] Header di ({hdr_cx}, {hdr_cy}), conf={conf:.4f}")
    print(f"[INFO] Item pertama: ({item_x}, {item_y}) = Y_header + {ITEM_OFFSET_Y}")

    jawab = input(f"Klik item di ({item_x}, {item_y})? (y/n): ").strip().lower()
    if jawab == 'y':
        tap(device, item_x, item_y)
        time.sleep(DELAY_AFTER_TAP)
        save_debug_screenshot(take_screenshot(device), "click_item_setelah")

        print("\n[INFO] Mengecek dialog yang muncul...")

        busy, _, _, bconf = find_template(device, TEMPLATE_BUSY, BUSY_THRESHOLD)
        if busy:
            print(f"[DETECTED] Builders busy! (conf={bconf:.4f})")
            return

        ug, ux, uy, uconf = find_template(device, TEMPLATE_UPGRADE, UPGRADE_THRESHOLD)
        if ug:
            print(f"[DETECTED] UPGRADE! (conf={uconf:.4f}) di ({ux}, {uy})")
            jawab2 = input("Mau klik Upgrade? (y/n): ").strip().lower()
            if jawab2 == 'y':
                tap(device, ux, uy)
                time.sleep(DELAY_AFTER_TAP)
                cf2, ccx2, ccy2, _ = find_template(device, TEMPLATE_CONFIRM, CONFIRM_THRESHOLD)
                if cf2:
                    tap(device, ccx2, ccy2)
                    print("[OK] Confirm diklik!")
            return

        print("[INFO] Tidak terdeteksi apapun. Mungkin perlu tunggu lebih lama?")


# ============================================================
#             MODE: DETECT UPGRADE
# ============================================================

def test_detect_upgrade(device):
    """Test deteksi tombol Upgrade. Dialog harus sudah terbuka!"""
    print("\n" + "=" * 60)
    print("  MODE: DETECT UPGRADE BUTTON")
    print("  Dialog upgrade harus sudah terbuka!")
    print("=" * 60 + "\n")

    save_debug_screenshot(take_screenshot(device), "upgrade_layar_awal")
    matches = find_all_matches(device, TEMPLATE_UPGRADE, UPGRADE_THRESHOLD)

    print(f"\n{'-' * 50}")
    print(f"  HASIL DETEKSI TOMBOL UPGRADE")
    print(f"{'-' * 50}")
    print(f"  Template   : {TEMPLATE_UPGRADE}")
    print(f"  Threshold  : {UPGRADE_THRESHOLD}")
    print(f"  Total      : {len(matches)} tombol ditemukan")
    print(f"{'-' * 50}")

    if matches:
        for i, (mx, my, mc) in enumerate(matches):
            print(f"  #{i+1}: ({mx}, {my}) conf={mc:.4f}")
        jawab = input(f"\nMau klik Upgrade #1 di ({matches[0][0]}, {matches[0][1]})? (y/n): ").strip().lower()
        if jawab == 'y':
            tap(device, matches[0][0], matches[0][1])
            time.sleep(DELAY_AFTER_TAP)
            save_debug_screenshot(take_screenshot(device), "upgrade_setelah_klik")
    else:
        print("  Tidak ada tombol Upgrade ditemukan di layar.")

    return matches


# ============================================================
#             MODE: CONFIRM ONLY
# ============================================================

def test_confirm_only(device):
    print("\n" + "=" * 60)
    print("  MODE: CONFIRM ONLY")
    print("  Pastikan layar SUDAH menampilkan dialog upgrade!")
    print("=" * 60 + "\n")

    ss = take_screenshot(device)
    h, w = ss.shape[:2]
    print(f"[INFO] Ukuran layar: {w} x {h}")
    save_debug_screenshot(ss, "confirm_layar_awal")

    found, cx, cy, conf = find_template(
        device, TEMPLATE_CONFIRM, CONFIRM_THRESHOLD
    )

    print(f"\n{'-' * 50}")
    print(f"  HASIL DETEKSI CONFIRM")
    print(f"{'-' * 50}")
    print(f"  Template   : {TEMPLATE_CONFIRM}")
    print(f"  Confidence : {conf:.4f}")
    print(f"  Threshold  : {CONFIRM_THRESHOLD}")
    print(f"  Status     : {'DITEMUKAN' if found else 'TIDAK DITEMUKAN'}")
    print(f"  Posisi     : ({cx}, {cy})")
    print(f"{'-' * 50}")

    if not found:
        print("\n[INFO] Mencoba threshold lebih rendah...")
        for t in [0.75, 0.70, 0.65, 0.60, 0.55, 0.50]:
            _, _, _, c = find_template(device, TEMPLATE_CONFIRM, t)
            if c >= t:
                print(f"  [!] Threshold {t}: MATCH (conf={c:.4f})")
                break
            else:
                print(f"  [ ] Threshold {t}: belum (conf={c:.4f})")

    if found:
        jawab = input("Mau klik tombol Confirm? (y/n): ").strip().lower()
        if jawab == 'y':
            tap(device, cx, cy)
            time.sleep(DELAY_AFTER_TAP)
            save_debug_screenshot(take_screenshot(device), "confirm_setelah_klik")

    return found, conf


# ============================================================
#             MODE: DETECT HEADER
# ============================================================

def test_detect_header(device):
    print("\n" + "=" * 60)
    print("  MODE: DETECT HEADER")
    print("  Pastikan menu Suggested upgrades sudah terbuka!")
    print("=" * 60 + "\n")

    save_debug_screenshot(take_screenshot(device), "header_layar_awal")

    found, cx, cy, conf = find_template(
        device, TEMPLATE_HEADER, HEADER_THRESHOLD
    )

    print(f"\n{'-' * 50}")
    print(f"  HASIL DETEKSI HEADER")
    print(f"{'-' * 50}")
    print(f"  Template   : {TEMPLATE_HEADER}")
    print(f"  Confidence : {conf:.4f}")
    print(f"  Status     : {'DITEMUKAN' if found else 'TIDAK DITEMUKAN'}")
    print(f"  Posisi     : ({cx}, {cy})")
    if found:
        print(f"  Item pertama Y: {cy + ITEM_OFFSET_Y}")
    print(f"{'-' * 50}")

    return found, cy


# ============================================================
#             MODE: CHECK BUSY
# ============================================================

def test_check_busy(device):
    print("\n" + "=" * 60)
    print("  MODE: CHECK BUILDERS BUSY")
    print("=" * 60 + "\n")

    save_debug_screenshot(take_screenshot(device), "busy_layar_awal")

    found, cx, cy, conf = find_template(
        device, TEMPLATE_BUSY, BUSY_THRESHOLD
    )

    print(f"\n{'-' * 50}")
    print(f"  HASIL DETEKSI BUILDERS BUSY")
    print(f"{'-' * 50}")
    print(f"  Template   : {TEMPLATE_BUSY}")
    print(f"  Confidence : {conf:.4f}")
    print(f"  Status     : {'TERDETEKSI' if found else 'TIDAK terdeteksi'}")
    if found:
        print(f"  Posisi     : ({cx}, {cy})")
        jawab = input("Mau tutup popup? (y/n): ").strip().lower()
        if jawab == 'y':
            tap(device, CLOSE_X, CLOSE_Y)
            print(f"[OK] Popup ditutup ({CLOSE_X}, {CLOSE_Y})")
    print(f"{'-' * 50}")

    return found


# ============================================================
#             MODE: SCREENSHOT ONLY
# ============================================================

def test_screenshot_only(device):
    print("\n" + "=" * 60)
    print("  MODE: SCREENSHOT ONLY")
    print("=" * 60 + "\n")

    ss = take_screenshot(device)
    h, w = ss.shape[:2]
    print(f"[INFO] Ukuran layar: {w} x {h}")
    path = save_debug_screenshot(ss, "screenshot")
    print(f"[OK] Disimpan di {path}")
    return True


# ============================================================
#             MODE: FULL FLOW
# ============================================================

def test_full_flow(device):
    """
    Flow bersih:
    LOOP:
      1. Klik Builder Head (450, 25) -> buka menu
      2. Scan "suggested_upgrades_text.png" -> (X, Y)
      3. Klik item pertama (X, Y + 28) -> view building
      4. Scan "upgrade_btn_dim.png" -> klik Upgrade
      5. Scan "confirm_text.png" -> klik Confirm
      6. Scan "all_builders_busy.png" -> busy = STOP
      7. Tidak busy -> ulang loop
    """
    print("\n" + "=" * 60)
    print("  MODE: FULL FLOW AUTO-UPGRADE")
    print("  Builder Head -> Header -> +28 -> Upgrade -> Confirm -> Busy?")
    print("=" * 60 + "\n")

    ok_count = 0
    skip_count = 0
    loop_count = 0

    print("[START] Mulai loop upgrade...\n")

    while True:
        loop_count += 1
        if MAX_LOOP > 0 and loop_count > MAX_LOOP:
            print(f"\n[STOP] Sudah {MAX_LOOP} loop (MAX_LOOP tercapai).")
            break

        print(f"\n{'=' * 50}")
        print(f"  LOOP #{loop_count}")
        print(f"{'=' * 50}")

        # --- 1: Klik Builder Head (setiap loop!) ---
        print(f"[1] Klik Builder Head ({BUILDER_HEAD_X}, {BUILDER_HEAD_Y})...")
        tap(device, BUILDER_HEAD_X, BUILDER_HEAD_Y)
        time.sleep(DELAY_MENU_LOAD)
        save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_builder")

        # --- 2: Scan header ---
        print(f"[2] Scan header 'Suggested upgrades'...")
        hdr_found, hdr_cx, hdr_cy, hconf = find_template(
            device, TEMPLATE_HEADER, HEADER_THRESHOLD
        )

        if not hdr_found:
            print("[SELESAI] Header tidak ditemukan. List kosong.")
            save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_no_header")
            break

        print(f"[OK] Header di ({hdr_cx}, {hdr_cy}), conf={hconf:.4f}")

        # --- 3: Klik item pertama (Y_header + 28) ---
        item_x = hdr_cx
        item_y = hdr_cy + ITEM_OFFSET_Y
        print(f"[3] Klik item: ({item_x}, {item_y}) = Y({hdr_cy}) + {ITEM_OFFSET_Y}")
        tap(device, item_x, item_y)
        time.sleep(DELAY_AFTER_TAP)
        save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_item_clicked")

        # --- 4: Cari tombol Upgrade ---
        print(f"[4] Cari tombol Upgrade...")
        ug, ux, uy, uconf = find_template(device, TEMPLATE_UPGRADE, UPGRADE_THRESHOLD)

        if not ug:
            skip_count += 1
            print(f"[SKIP] Upgrade tidak ditemukan (conf={uconf:.4f})")
            print(f"       Menutup dialog...")
            tap(device, CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_skip")
            continue

        print(f"[OK] Upgrade ditemukan di ({ux}, {uy}), conf={uconf:.4f}")
        tap(device, ux, uy)
        time.sleep(DELAY_AFTER_TAP)

        # --- 5: Cari Confirm setelah klik Upgrade ---
        print(f"[5] Cari Confirm setelah klik Upgrade...")
        cf, ccx, ccy, cconf = find_template(device, TEMPLATE_CONFIRM, CONFIRM_THRESHOLD)

        if not cf:
            skip_count += 1
            print(f"[SKIP] Confirm tidak muncul (conf={cconf:.4f})")
            print(f"       Menutup dialog...")
            tap(device, CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_no_confirm")
            continue

        print(f"[OK] Confirm ditemukan! ({ccx}, {ccy}), conf={cconf:.4f}")
        tap(device, ccx, ccy)
        time.sleep(DELAY_AFTER_TAP)

        # --- 6: Cek busy SETELAH klik Confirm ---
        print(f"[6] Cek busy...")
        busy, _, _, bconf = find_template(device, TEMPLATE_BUSY, BUSY_THRESHOLD)
        if busy:
            print(f"[STOP] All builders are busy! (conf={bconf:.4f})")
            tap(device, CLOSE_X, CLOSE_Y)
            time.sleep(DELAY_AFTER_CLOSE)
            save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_busy_stop")
            break

        # Tidak busy = berhasil
        ok_count += 1
        print(f"[OK] Upgrade #{ok_count} BERHASIL!")
        save_debug_screenshot(take_screenshot(device), f"flow_loop{loop_count}_ok")

    # =====================================================
    # RINGKASAN
    # =====================================================
    print(f"\n{'=' * 50}")
    print(f"  RINGKASAN FULL FLOW")
    print(f"{'=' * 50}")
    print(f"  Total loop       : {loop_count}")
    print(f"  Upgrade berhasil : {ok_count}")
    print(f"  Dilewati/skip    : {skip_count}")
    print(f"{'=' * 50}")


# ============================================================
#                       MAIN
# ============================================================

def main():
    print(f"\n{'=' * 60}")
    print(f"  TEST AUTO-UPGRADE - Clash of Clans Bot")
    print(f"{'=' * 60}")
    print(f"  Mode       : {MODE}")
    print(f"  Base dir   : {BASE_DIR}")
    print(f"  Gambar dir : {GAMBAR_DIR}")
    print(f"  Debug dir  : {DEBUG_DIR}")
    print(f"  Template   : Confirm={TEMPLATE_CONFIRM}")
    print(f"               Header={TEMPLATE_HEADER}")
    print(f"               Upgrade={TEMPLATE_UPGRADE}")
    print(f"               Busy={TEMPLATE_BUSY}")
    print(f"  Threshold  : Confirm={CONFIRM_THRESHOLD} | "
          f"Header={HEADER_THRESHOLD}")
    print(f"               Upgrade={UPGRADE_THRESHOLD} | "
          f"Busy={BUSY_THRESHOLD}")
    print(f"  Builder Head : ({BUILDER_HEAD_X}, {BUILDER_HEAD_Y})")
    print(f"  Item offset  : {ITEM_OFFSET_Y}px")
    print(f"{'=' * 60}\n")

    if not os.path.isdir(GAMBAR_DIR):
        print(f"[ERROR] Folder Gambar tidak ada: {GAMBAR_DIR}")
        sys.exit(1)

    templates = [TEMPLATE_CONFIRM, TEMPLATE_HEADER, TEMPLATE_UPGRADE, TEMPLATE_BUSY]
    for t in templates:
        p = os.path.join(GAMBAR_DIR, t)
        status = "OK" if os.path.exists(p) else "MISSING!"
        print(f"  [{status}] {t}")

    print()
    device = connect_adb()

    mode_map = {
        "confirm_only":    test_confirm_only,
        "detect_header":   test_detect_header,
        "detect_upgrade":  test_detect_upgrade,
        "check_busy":      test_check_busy,
        "click_item":      test_click_item,
        "screenshot_only": test_screenshot_only,
        "full_flow":       test_full_flow,
    }

    if MODE not in mode_map:
        print(f"[ERROR] Mode tidak dikenal: '{MODE}'")
        print(f"[INFO] Tersedia: {', '.join(mode_map.keys())}")
        sys.exit(1)

    mode_map[MODE](device)


if __name__ == "__main__":
    main()