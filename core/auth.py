import os
import sys
import json
import time
import uuid
import hashlib
import platform
import threading
import subprocess

from core.config import (
    FIREBASE_SECRET, SESSION_FILE, HWID_FILE, SETTINGS_URL,
    CYAN, ORANGE, GREEN, RED, BOLD, DIM, RESET, ADVANCE_PASSWORD_HASH
)

def get_cloud_setting(key, default_val):
    try:
        import requests
        res = requests.get(SETTINGS_URL, timeout=8).json()
        if isinstance(res, dict) and key in res:
            return res[key]
    except: pass
    return default_val

def get_hwid():
    if os.path.exists(HWID_FILE):
        try:
            with open(HWID_FILE, 'r') as f:
                return f.read().strip()
        except: pass
    raw_id = platform.node() + str(uuid.getnode())
    hwid = hashlib.md5(raw_id.encode()).hexdigest()[:15].upper()
    try:
        with open(HWID_FILE, 'w') as f:
            f.write(hwid)
    except: pass
    return hwid

def send_activity_log(action_msg):
    try:
        import requests
        hwid = get_hwid()
        db_url = f"https://termux-control-default-rtdb.asia-southeast1.firebasedatabase.app/Users/{hwid}/activity_logs.json?auth={FIREBASE_SECRET}"
        timestamp = time.strftime("%Y-%m-%d %I:%M:%S %p")
        log_data = {str(int(time.time())): f"[{timestamp}] {action_msg}"}
        requests.patch(db_url, json=log_data, timeout=5)
    except: pass

def ping_server_and_check_ban(hwid, original_pass):
    import requests
    db_url = f"https://termux-control-default-rtdb.asia-southeast1.firebasedatabase.app/Users/{hwid}.json?auth={FIREBASE_SECRET}"
    while True:
        try:
            res = requests.get(db_url, timeout=10).json()
            if isinstance(res, dict):
                if res.get("status") == "Banned":
                    print(f"\n\n{RED}{BOLD}admin ban you not use this tool 💥 admin ban korse Abdullah Al Hasib{RESET}")
                    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
                    os._exit(1)
                elif res.get("password") != original_pass:
                    print(f"\n\n{RED}{BOLD}Password has been changed by Admin! Please login again.{RESET}")
                    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
                    os._exit(1)
            requests.patch(db_url, json={"last_ping": int(time.time())}, timeout=5)
        except: pass
        time.sleep(10) 

def start_online_ping(hwid, original_pass):
    t = threading.Thread(target=ping_server_and_check_ban, args=(hwid, original_pass), daemon=True)
    t.start()

def check_firebase_approval():
    import requests
    hwid = get_hwid()
    
    try:
        brand = subprocess.getoutput('getprop ro.product.brand').strip().capitalize()
        model = subprocess.getoutput('getprop ro.product.model').strip()
        device_name = f"{brand} {model}".strip() if brand else platform.node()
    except: device_name = platform.node()
        
    base_url = "https://termux-control-default-rtdb.asia-southeast1.firebasedatabase.app/Users"

    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f: session_data = json.load(f)
            if session_data.get("hwid") == hwid:
                res = requests.get(f"{base_url}/{hwid}.json?auth={FIREBASE_SECRET}", timeout=5).json()
                if isinstance(res, dict) and res.get("status") in ["Approved", "VIP"] and res.get("password") == session_data.get("password"):
                    print(f"\n{GREEN}[✓] Auto-Login Successful! Welcome back.{RESET}")
                    start_online_ping(hwid, session_data.get("password"))
                    return True
                else: os.remove(SESSION_FILE)
        except: pass

    print(f"\n{CYAN}[USER LOGIN]{RESET} Please login to your account.")
    user_email = input(f"{BOLD}{ORANGE}📧 Enter Your Email: {RESET}").strip()
    user_password = input(f"{BOLD}{ORANGE}🔑 Enter Your Password: {RESET}").strip()
    
    if not user_email or not user_password:
        print(f"{RED}[!] Email and Password cannot be empty!{RESET}"); return False
        
    print(f"\n{CYAN}[SYSTEM]{RESET} Your Hardware ID: {BOLD}{ORANGE}{hwid}{RESET}")
    
    try:
        all_users = requests.get(f"{base_url}.json?auth={FIREBASE_SECRET}", timeout=10).json()
        if isinstance(all_users, dict) and "error" in all_users: return False
        if all_users is None: all_users = {}
            
        existing_hwid = None
        db_status = "Pending"
        
        for db_id, data in all_users.items():
            if isinstance(data, dict) and data.get("email") == user_email:
                existing_hwid = db_id
                if data.get("password") != user_password:
                    print(f"\n{RED}[✗] Invalid Password for this Email!{RESET}"); return False
                db_status = data.get("status", "Pending")
                break

        if existing_hwid:
            if db_status in ["Approved", "VIP"]:
                print(f"\n{GREEN}[✓] Login Successful! Welcome back. Approved by Cbr tool owner Abdullah Al Hasib{RESET}"); time.sleep(1.5)
                payload = all_users[existing_hwid]
                payload["device_name"] = device_name 
                payload["last_ping"] = int(time.time())
                
                if existing_hwid != hwid:
                    payload["hwid"] = hwid
                    requests.put(f"{base_url}/{hwid}.json?auth={FIREBASE_SECRET}", json=payload)
                    requests.delete(f"{base_url}/{existing_hwid}.json?auth={FIREBASE_SECRET}")
                else:
                    requests.patch(f"{base_url}/{hwid}.json?auth={FIREBASE_SECRET}", json={"device_name": device_name, "last_ping": int(time.time())})
                    
                with open(SESSION_FILE, "w") as f: json.dump({"hwid": hwid, "email": user_email, "password": user_password}, f)
                start_online_ping(hwid, user_password)
                send_activity_log("User Logged In Successfully")
                return True
            elif db_status == "Banned":
                print(f"\n{RED}{BOLD}admin ban you not use this tool 💥 admin ban korse Abdullah Al Hasib{RESET}"); return False
        else:
            payload = {"status": "Pending", "hwid": hwid, "email": user_email, "password": user_password, "device_name": device_name, "last_ping": int(time.time())}
            requests.put(f"{base_url}/{hwid}.json?auth={FIREBASE_SECRET}", json=payload)
            existing_hwid = hwid
            send_activity_log("New Registration Created - Pending Approval")

        is_waiting = False
        db_url = f"{base_url}/{existing_hwid}.json?auth={FIREBASE_SECRET}"
        while True:
            try: data = requests.get(db_url, timeout=10).json()
            except KeyboardInterrupt: print(f"\n{RED}[!] Login cancelled by user.{RESET}"); return False
            except: time.sleep(3); continue
                
            if not data: time.sleep(3); continue
            status = data.get("status", "Pending")
            
            if status in ["Approved", "VIP"]:
                print(f"\n{GREEN}[✓] Login Successful! Approved by Cbr tool owner Abdullah Al Hasib{RESET}"); time.sleep(1.5)
                payload = data; payload["device_name"] = device_name
                if existing_hwid != hwid:
                    payload["hwid"] = hwid
                    requests.put(f"{base_url}/{hwid}.json?auth={FIREBASE_SECRET}", json=payload)
                    requests.delete(f"{base_url}/{existing_hwid}.json?auth={FIREBASE_SECRET}")
                else:
                    requests.patch(f"{base_url}/{hwid}.json?auth={FIREBASE_SECRET}", json={"device_name": device_name})
                    
                with open(SESSION_FILE, "w") as f: json.dump({"hwid": hwid, "email": user_email, "password": user_password}, f)
                start_online_ping(hwid, user_password); send_activity_log("User Approved and Logged In")
                return True
            elif status == "Banned":
                print(f"\n{RED}{BOLD}admin ban you not use this tool 💥 admin ban korse Abdullah Al Hasib{RESET}"); return False
            else:
                if not is_waiting: print(f"{CYAN}[SYSTEM]{RESET} Waiting for Admin Approval", end="", flush=True); is_waiting = True
                print(".", end="", flush=True); time.sleep(3) 
    except Exception: 
        print(f"\n{RED}[!] Network error during login.{RESET}")
        return False

def verify_admin_access():
    live_admin_pass = get_cloud_setting('admin_password', None)
    admin_pass = input(f"{BOLD}{ORANGE}🔑 Enter Admin Password: {RESET}").strip()
    if (live_admin_pass and admin_pass == live_admin_pass) or hashlib.sha256(admin_pass.encode()).hexdigest() == ADVANCE_PASSWORD_HASH: return True
    print(f"\n{RED}[✗] Access Denied!{RESET}"); time.sleep(2); return False
