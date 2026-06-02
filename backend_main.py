"""
Point d'entrée du backend CHUbot pour PyInstaller et le sidecar Tauri.

Utilisé pour :
  - Dev  : python backend_main.py
  - Prod : PyInstaller → chubot-backend.exe (démarré par Tauri comme sidecar)
"""

import sys
import os

# Quand PyInstaller emballe l'app, les ressources sont dans sys._MEIPASS
if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS
    os.chdir(base_dir)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "bot.api.app:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
        access_log=False,
    )
