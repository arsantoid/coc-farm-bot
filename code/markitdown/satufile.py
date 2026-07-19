from markitdown import MarkItDown

md = MarkItDown()

# 1. Paste "Relative Path" kamu di sini, jangan lupa tambahkan r di depan kutip
path_gambar = r"code\markitdown\file\Screenshot 2026-06-28 153831.png" # Sesuaikan nama lengkap filenya

# Konversi file
hasil = md.convert(path_gambar)

# Cetak hasil di terminal
print(hasil.text_content)

# 2. Tentukan lokasi simpan. 
# Pakai path ke folder output supaya tidak berantakan di luar.
path_simpan = r"code\markitdown\output\hasil_screenshot.md"

with open(path_simpan, "w", encoding="utf-8") as f:
    f.write(hasil.text_content)