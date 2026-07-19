import cv2
import numpy as np
from ppadb.client import Client as AdbClient

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("❌ Emulator tidak terdeteksi!")
    exit()

device = devices[0]

screencap = device.screencap()
img = cv2.imdecode(np.frombuffer(screencap, np.uint8), cv2.IMREAD_COLOR)

# ==========================================
# ISI KOORDINAT YANG MAU DICEK DI SINI
# Format: img[Y, X]
# ==========================================
Y = 140
X = 910
# ==========================================

b, g, r = img[Y, X]

punya_de = (r < 80 and g < 80 and b < 80)

print(f"Koordinat : [{Y}, {X}]")
print(f"RGB       : R={r} G={g} B={b}")
print(f"Deteksi   : {'ADA DE' if punya_de else 'TIDAK ADA DE'}")