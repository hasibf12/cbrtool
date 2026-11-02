#!/usr/bin/env python3
import os
import sys
import time

# Core ফোল্ডার থেকে সিকিউরিটি, কালার এবং ব্যাসিক জিনিসগুলো ইম্পোর্ট করা হচ্ছে
from core.config import premium_header, CYAN, GREEN, ORANGE, RED, PURPLE, RESET, BOLD, DIM
from core.utils import check_dependencies, setup_otg_drivers, check_fastboot
from core.auth import check_firebase_approval

# Modules ফোল্ডার থেকে ফ্ল্যাশ ইঞ্জিন ইম্পোর্ট করা হচ্ছে
try:
    from modules.flash_stock import cbr_smart_flasher
except ImportError as e:
    print(f"Error loading modules: {e}")

def main_menu():
    while True:
        premium_header()
        print(f"{CYAN} [1]{RESET} Bootloader Unlock")
        print(f"{CYAN} [2]{RESET} CBR WIFI (Setup)") 
        print(f"{CYAN} [3]{RESET} ⚡ ADVANCE ONLY CBR OWNER ABDULLAH AL HASIB ⚡") 
        print(f"{GREEN} [5]{RESET} 📱 Redmi ROM Flash (Native Engine)") 
        print(f"{GREEN} [6]{RESET} 📱 Infinix Stock Flash (FastbootD Engine)") 
        print(f"{ORANGE} [7]{RESET} 🧪 Brom Mode Test Any")
        print(f"{ORANGE} [8]{RESET} 🪦 Only Dead -> Go Fastboot")
        print(f"{ORANGE} [9]{RESET} 🪦 Dead Go Fastboot Flash Combo")
        print(f"{ORANGE} [66]{RESET} {BOLD}Apply Mi Unlock Permission{RESET}")
        print(f"{RED} [99]{RESET} {BOLD}Admin Control Panel{RESET}")
        print(f"{CYAN} [0]{RESET} Exit")
        
        choice = input(f"\n{BOLD}{ORANGE}👉 Select an option: {RESET}").strip()
        
        if choice == '5':
            cbr_smart_flasher(brand="redmi")
        elif choice == '6':
            cbr_smart_flasher(brand="infinix")
        elif choice == '0':
            print(f"\n{GREEN}Thanks for using CBR Tool!{RESET}")
            sys.exit(0)
        else:
            print(f"\n{ORANGE}[!] This module is not added to GitHub yet. We will add it soon!{RESET}")
            time.sleep(2)

def run_tool():
    try:
        # টুল রান হওয়ার শুরুতেই ডিপেন্ডেন্সি এবং লগিন চেক করবে
        check_dependencies()
        setup_otg_drivers()
        
        if not check_firebase_approval():
            input(f"\n{RED}Press Enter to exit...{RESET}")
            sys.exit(1)
            
        check_fastboot()
        main_menu()
        
    except Exception as fatal_err:
        print(f"\n{RED}[CRITICAL ERROR]: {str(fatal_err)}{RESET}")
        if sys.platform != "win32":
            os.system("termux-wake-unlock > /dev/null 2>&1")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    run_tool()
