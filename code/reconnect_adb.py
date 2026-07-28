"""ADB reconnect helper - reconnect to existing ADB server"""
import subprocess
import time
import os
import shutil

# Auto-detect ADB path
def find_adb():
    """Find adb.exe dynamically."""
    user_profile = os.environ.get("USERPROFILE", "C:\\")
    candidates = [
        os.path.join(user_profile, "platform-tools", "adb.exe"),
        os.path.join(user_profile, "AppData", "Local", "Android", "Sdk", "platform-tools", "adb.exe"),
        r"C:\Android\platform-tools\adb.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # Try PATH
    which = shutil.which("adb")
    if which:
        return which
    return "adb"  # fallback, will fail if not in PATH

ADB_PATH = find_adb()
LD_PORT = "127.0.0.1:5555"
BS_PORT = "127.0.0.1:5556"


def reconnect_adb():
    """Reconnect to emulator. DON'T kill ADB servers (breaks BlueStacks). Returns (success, client, device)."""
    import socket

    # 1. Find open emulator ports
    open_ports = []
    for port in range(5555, 5570):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            open_ports.append(port)
        s.close()

    # 2. Connect to found ports using standard adb
    for port in open_ports:
        addr = f"127.0.0.1:{port}"
        subprocess.run([ADB_PATH, "connect", addr], capture_output=True)
        time.sleep(0.5)

    # 3. Try ppadb on port 5037
    for attempt in range(3):
        try:
            from ppadb.client import Client as AdbClient
            client = AdbClient(host="127.0.0.1", port=5037)
            devices = client.devices()
            if devices:
                print(f"ADB reconnected: {devices[0].serial}")
                return True, client, devices[0]
        except Exception as e:
            print(f"ADB reconnect attempt {attempt+1} failed: {e}")
            time.sleep(2)

    print("ADB reconnect failed after 3 attempts")
    return False, None, None
