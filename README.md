# 🏰 CoC Auto Farm + Upgrade Bot (v4)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Bot otomatis untuk **Clash of Clans** berbasis **Image Recognition (Template Matching)** dan **ADB**.  
Dirancang untuk berjalan di **LDPlayer** (resolusi 960x540 / 960x640) tanpa OCR, sangat ringan (RAM ~8GB).

## ✨ Fitur Utama
- 🔄 **Multi-Account** (Support 15+ akun dengan switch otomatis)
- ⚔️ **Farming Otomatis** (Cari match, deploy pasukan, surrender, dan loot)
- 🏠 **Upgrade Bangunan Prioritas** (Hero, Lab, Storage, Clan Castle, dll)
- 🔬 **Upgrade Lab Prioritas** (Dragon, Archer, Barbarian, Freeze Spell, dll)
- 🛡️ **Penanganan Error** (Deteksi Connection Lost, Force Restart CoC, Clear Popup Event)
- 🔍 **Anti-Zoom** (Multi-scale matching 0.98, 1.0, 1.02)
- 💾 **State Persistence** (Menyimpan progress battle/upgrade per akun di `account_config.json`)

## 📋 Prasyarat
1.  **LDPlayer** terinstal dan sudah di-setup dengan Clash of Clans.
2.  **ADB** terinstal dan path `adb` sudah terdeteksi sistem.
3.  **Python 3.8+** terinstal.
4.  Resolusi emulator **960x540** atau **960x640** (sesuai template).

## 🚀 Cara Instalasi & Menjalankan

1.  **Clone repository ini** (atau download zip):
    ```bash
    git clone https://github.com/ryanchandra1/Clash_Of_Clans_Automation.git
    cd Clash_Of_Clans_Automation