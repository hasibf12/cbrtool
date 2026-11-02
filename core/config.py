import os
import hashlib
import platform

# 💻 DUAL-CORE ARCHITECTURE DETECTOR 📱
IS_WINDOWS = (platform.system().lower() == "windows")

# Colors
CYAN = "\033[36m"
ORANGE = "\033[38;5;208m"
GREEN = "\033[1;32m"
RED = "\033[1;31m"
PURPLE = "\033[35m"
HACKER_GREEN = "\033[38;5;46m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

SECURE_PASSWORD_HASH = "ed30e4a879af03333d3ba7a782b941bb92ce5fba9d6c60be387c1688e2b5ea40"
ADVANCE_PASSWORD_HASH = hashlib.sha256(bytes.fromhex("6362723031393736363334303435")).hexdigest()

FIREBASE_SECRET = "W2u5TaOnnVWpdOwkCSsLDPuUzrXnSiC0o7ngf7zJ"
SETTINGS_URL = f"https://termux-control-default-rtdb.asia-southeast1.firebasedatabase.app/Settings.json?auth={FIREBASE_SECRET}"
SESSION_FILE = os.path.expanduser("~/.cbr_session.json")
HWID_FILE = os.path.expanduser("~/.cbr_hwid")

def premium_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{CYAN}{BOLD}")
    print(r"  ██████╗██████╗ ██████╗ ")
    print(r" ██╔════╝██╔══██╗██╔══██╗")
    print(r" ██║     ██████╔╝██████╔╝")
    print(r" ██║     ██╔══██╗██╔══██╗")
    print(r" ╚██████╗██████╔╝██║  ██║")
    print(r"  ╚═════╝╚═════╝ ╚═╝  ╚═╝")
    print(f"      ⚡ CBR TOOL ⚡     {RESET}")
    if IS_WINDOWS:
        print(f" {HACKER_GREEN}{BOLD}[ACTIVE MODE: WINDOWS SUPER-PC]{RESET}")
    else:
        print(f" {HACKER_GREEN}{BOLD}[ACTIVE MODE: TERMUX MOBILE]{RESET}")
    print(f"{ORANGE}{BOLD} © Copyright: Abdullah Al Hasib {RESET}")
    print(f"{ORANGE}{BOLD} WhatsApp :+8801976634045 {RESET}")
    print(f"{DIM}{'━' * 35}{RESET}\n")
