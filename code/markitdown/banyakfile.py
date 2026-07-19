from markitdown import MarkItDown
import os

md = MarkItDown()
folder = r"code\markitdown\file"

# --- UBAH BAGIAN INI ---
# Tambahkan path lengkapnya agar masuk ke dalam folder markitdown
output_dir = r"code\markitdown\output" 
# -----------------------

# Perintah ini akan membuat folder 'output' di dalam 'code\markitdown'
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(folder):
    filepath = os.path.join(folder, filename)
    try:
        hasil = md.convert(filepath)
        nama_output = os.path.splitext(filename)[0] + ".md"
        
        # Gabungkan path folder output dengan nama file
        path_simpan = os.path.join(output_dir, nama_output)
        
        with open(path_simpan, "w", encoding="utf-8") as f:
            f.write(hasil.text_content)
            
        print(f"Berhasil: {filename}")
        
    except Exception as e:
        print(f"Gagal: {filename} - {e}")