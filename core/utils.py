import os
import sys
import time
import subprocess
import shutil
import json
import platform

from core.config import IS_WINDOWS, CYAN, ORANGE, GREEN, RED, PURPLE, RESET, BOLD, DIM

DEVNULL = subprocess.DEVNULL
ACTIVE_USB_DEV = None
GRANTED_USB_DEVS = set()

def check_dependencies():
    if not IS_WINDOWS:
        bin_dir = "/data/data/com.termux/files/usr/bin"
        shortcut_path = os.path.join(bin_dir, "cbrtool")
        script_path = os.path.abspath(sys.argv[0]) # Auto detect main path
        if os.path.exists(bin_dir):
            try:
                with open(shortcut_path, "w") as f:
                    f.write(f"#!/bin/bash\npython3 '{script_path}' \"$@\"\n")
                os.chmod(shortcut_path, 0o755)
            except: pass
            
        try:
            import ssl
        except ImportError:
            print(f"{ORANGE}[*] Repairing Termux SSL...{RESET}")
            subprocess.call(["pkg", "update", "-y"], stdout=DEVNULL, stderr=DEVNULL)
            subprocess.call(["pkg", "install", "openssl", "ca-certificates", "python", "-y"], stdout=DEVNULL, stderr=DEVNULL)
    
    try:
        import colorama, Cryptodome, miunlock, requests 
    except ImportError:
        print(f"{ORANGE}[*] Installing basic libraries silently...{RESET}")
        subprocess.call([sys.executable, "-m", "pip", "install", "colorama", "pycryptodomex", "miunlock", "requests", "--no-warn-script-location", "--break-system-packages"], stdout=DEVNULL, stderr=DEVNULL)

    if not IS_WINDOWS:
        try:
            import mtkclient
        except ImportError:
            print(f"{ORANGE}[*] Installing BROM Engine silently (mtkclient)...{RESET}")
            res = subprocess.call([sys.executable, "-m", "pip", "install", "mtkclient", "--no-deps", "--no-warn-script-location", "--break-system-packages"], stdout=DEVNULL, stderr=DEVNULL)
            if res != 0:
                subprocess.call([sys.executable, "-m", "pip", "install", "https://github.com/bkerler/mtkclient/archive/main.zip", "--no-deps", "--no-warn-script-location", "--break-system-packages"], stdout=DEVNULL, stderr=DEVNULL)
                subprocess.call([sys.executable, "-m", "pip", "install", "pycryptodome", "pyusb", "colorama", "--no-warn-script-location", "--break-system-packages"], stdout=DEVNULL, stderr=DEVNULL)
    else:
        mtk_bin = shutil.which("mtk")
        if not mtk_bin:
            scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
            if not os.path.exists(os.path.join(scripts_dir, "mtk.exe")):
                print(f"{ORANGE}[*] Installing BROM Engine silently (mtkclient)...{RESET}")
                subprocess.call([sys.executable, "-m", "pip", "install", "mtkclient", "--no-warn-script-location"], stdout=DEVNULL, stderr=DEVNULL)

def setup_otg_drivers():
    if not IS_WINDOWS:
        try:
            if shutil.which("lsusb") is None: subprocess.call(["pkg", "install", "usbutils", "-y"], stdout=DEVNULL, stderr=DEVNULL)
            if not os.path.exists("/data/data/com.termux/files/usr/bin/termux-usb"):
                subprocess.call(["pkg", "install", "termux-api", "libusb", "-y"], stdout=DEVNULL, stderr=DEVNULL)
            if not os.path.exists("/data/data/com.termux/files/usr/bin/termux-fastboot"):
                os.system("curl -fsS https://raw.githubusercontent.com/nohajc/termux-adb/master/install.sh | bash > /dev/null 2>&1")
        except: pass

def get_fastboot_bin():
    if not IS_WINDOWS and shutil.which("termux-fastboot") is not None:
        return "termux-fastboot"
    return "fastboot"

def trigger_otg_popup(silent=False, force=False):
    global ACTIVE_USB_DEV, GRANTED_USB_DEVS
    if IS_WINDOWS: return False
    if shutil.which("termux-usb") is not None:
        try:
            res = subprocess.run(["termux-usb", "-l"], capture_output=True, text=True, timeout=5)
            if res.stdout and res.stdout.strip():
                usb_devs = json.loads(res.stdout.strip())
                if isinstance(usb_devs, list):
                    GRANTED_USB_DEVS.intersection_update(set(usb_devs))
                    if len(usb_devs) > 0:
                        ACTIVE_USB_DEV = usb_devs[-1]
                        for dev in usb_devs:
                            if dev in GRANTED_USB_DEVS and not force: continue
                            if not silent: print(f"{CYAN}[OTG]{RESET} Requesting USB Permission for {dev}...")
                            req = subprocess.run(["termux-usb", "-r", dev], capture_output=True, text=True, timeout=12)
                            req_out = ((req.stdout or "") + (req.stderr or "")).lower()
                            if "granted" in req_out or "yes" in req_out or (req.returncode == 0 and "denied" not in req_out):
                                GRANTED_USB_DEVS.add(dev)
                                ACTIVE_USB_DEV = dev
                                if not silent: print(f"{GREEN}[✓] OTG Permission Locked!{RESET}")
                        time.sleep(0.5)
                        return True
                    else: ACTIVE_USB_DEV = None
        except: pass
    return False

def run_usb_fastboot_probe(fb_bin, args_list, timeout_sec=10):
    global ACTIVE_USB_DEV
    try:
        res = subprocess.run([fb_bin] + args_list, capture_output=True, text=True, timeout=timeout_sec)
        comb = ((res.stdout or "") + "\n" + (res.stderr or "")).strip()
        if comb and "waiting for any device" not in comb.lower() and "no permissions" not in comb.lower():
            return comb
    except: pass

    if not IS_WINDOWS and fb_bin != "termux-fastboot" and shutil.which("termux-fastboot") is not None:
        try:
            res2 = subprocess.run(["termux-fastboot"] + args_list, capture_output=True, text=True, timeout=timeout_sec)
            comb2 = ((res2.stdout or "") + "\n" + (res2.stderr or "")).strip()
            if comb2 and "waiting for" not in comb2.lower() and "no permissions" not in comb2.lower():
                return comb2
        except: pass
    return ""

def check_fastboot():
    if shutil.which("fastboot") is None and shutil.which("termux-fastboot") is None:
        print(f"{RED}[!] Fastboot is not installed!{RESET}")
        if not IS_WINDOWS:
            print(f"{ORANGE}[*] Auto-installing...{RESET}")
            os.system("pkg update -y > /dev/null 2>&1 && pkg install android-tools -y > /dev/null 2>&1")
        else: sys.exit(1)

def wait_and_connect_fastboot():
    print(f"\n{CYAN}[SYSTEM]{RESET} Checking Fastboot Connection...")
    print(f"{DIM}Please connect your phone in Fastboot mode.{RESET}")
    start_time = time.time()
    retry_count = 0
    while True:
        trigger_otg_popup(silent=True, force=(not GRANTED_USB_DEVS))
        fb_bin = get_fastboot_bin()
        out = run_usb_fastboot_probe(fb_bin, ["devices"], timeout_sec=5)
        if out and "fastboot" in out.lower() and "permission" not in out.lower():
            print(f"\n{GREEN}[✓] Device Connected Successfully in Fastboot Mode!{RESET}")
            return True
        sys.stdout.write(f"\r\033[K{ORANGE}[WAITING]{RESET} Polling for fastboot device...")
        sys.stdout.flush()
        
        retry_count += 1
        if retry_count > 15:
            print(f"\n{RED}[!] Timeout: Make sure device is in Fastboot Mode and OTG is on.{RESET}")
            ans = input(f"{ORANGE}Press 'r' to retry, or any key to cancel: {RESET}").strip().lower()
            if ans == 'r':
                retry_count = 0
            else:
                return False
        time.sleep(2)

def get_device_info():
    global ACTIVE_USB_DEV, GRANTED_USB_DEVS
    print(f"{CYAN}[INFO]{RESET} Fetching device details...")
    for attempt in range(5):
        fb_bin = get_fastboot_bin()
        trigger_otg_popup(force=(attempt > 0 and not GRANTED_USB_DEVS))
        dev_out = run_usb_fastboot_probe(fb_bin, ["devices"], timeout_sec=5)
        if dev_out and "fastboot" in dev_out.lower() and "permission" not in dev_out.lower():
            first_line = dev_out.splitlines()[0].strip()
            prod_out = run_usb_fastboot_probe(fb_bin, ["getvar", "product"], timeout_sec=3)
            p_name = prod_out.split("product:")[1].split()[0].strip() if "product:" in prod_out else first_line.split()[0].strip()
            print(f"{GREEN}[✓] Connected Device: {p_name}{RESET}")
            return p_name

        for var_name in ["product", "is-userspace", "serialno"]:
            var_out = run_usb_fastboot_probe(fb_bin, ["getvar", var_name], timeout_sec=4)
            if f"{var_name}:" in var_out.lower() or "okay" in var_out.lower():
                dev_label = f"Fastboot-Device ({ACTIVE_USB_DEV})" if ACTIVE_USB_DEV else "Fastboot-Device"
                print(f"{GREEN}[✓] Connected Device: {dev_label}{RESET}")
                return dev_label
        time.sleep(2)
    return None

def get_brom_device_info():
    global ACTIVE_USB_DEV, GRANTED_USB_DEVS
    print(f"{CYAN}[BROM-SCAN]{RESET} Waiting for MTK BROM Connection...")
    print(f"{ORANGE}[*] Please turn OFF phone. Hold VOLUME UP + DOWN and connect USB cable!{RESET}")
    
    end_time = time.time() + 60
    if IS_WINDOWS:
        while time.time() < end_time:
            found = False
            try:
                res = subprocess.run("wmic path Win32_PnPEntity get Caption,DeviceID", shell=True, capture_output=True, text=True, creationflags=0x08000000)
                if res.returncode == 0 and ("VID_0E8D" in res.stdout.upper() or "MediaTek" in res.stdout): found = True
            except: pass
            
            if not found:
                try:
                    res2 = subprocess.run(["powershell", "-Command", "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match 'VID_0E8D' -or $_.Class -match 'Ports' }"], capture_output=True, text=True, creationflags=0x08000000)
                    if res2.returncode == 0 and ("MediaTek" in res2.stdout or "VID_0E8D" in res2.stdout.upper()): found = True
                except: pass
            
            if found:
                print(f"\n{GREEN}[✓] MediaTek BROM Port Detected!{RESET}")
                return True
                
            sys.stdout.write(f"\r\033[K{ORANGE}>> Windows Fast Polling for BROM Port... ({int(end_time - time.time())}s){RESET}")
            sys.stdout.flush()
            time.sleep(0.5)
    else:
        while time.time() < end_time:
            if shutil.which("termux-usb") is not None:
                try:
                    res = subprocess.run(["termux-usb", "-l"], capture_output=True, text=True, timeout=2)
                    if res.stdout and res.stdout.strip():
                        usb_devs = json.loads(res.stdout.strip())
                        if usb_devs:
                            ACTIVE_USB_DEV = usb_devs[-1]
                            print(f"\n{GREEN}[✓] Device Detected in BROM Mode!{RESET}")
                            req = subprocess.run(["termux-usb", "-r", ACTIVE_USB_DEV], capture_output=True, text=True, timeout=5)
                            if "granted" in req.stdout.lower() or req.returncode == 0:
                                GRANTED_USB_DEVS.add(ACTIVE_USB_DEV)
                                return True
                except: pass
            sys.stdout.write(f"\r\033[K{ORANGE}>> Ninja Polling for BROM Port... ({int(end_time - time.time())}s){RESET}")
            sys.stdout.flush()
            time.sleep(0.5)
    print(f"\n{RED}[!] Failed to catch BROM port within 60 seconds.{RESET}")
    return False
