import os
import sys
import time
import subprocess
import shutil
import tarfile
import zipfile
import glob
import re

from core.config import (
    CYAN, ORANGE, GREEN, RED, PURPLE, HACKER_GREEN, RESET, BOLD, DIM, IS_WINDOWS
)
import core.utils as utils
from core.auth import send_activity_log, get_cloud_setting

def cbr_smart_flasher(brand="redmi"):
    if brand == "redmi":
        _cbr_redmi_native()
    elif brand == "infinix":
        _cbr_infinix_native()

# ==========================================
# 🚀 REDMI NATIVE FLASH ENGINE (FROM BACKUP) 🚀
# ==========================================
def _cbr_redmi_native():
    if not IS_WINDOWS: os.system("termux-wake-lock > /dev/null 2>&1")
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{PURPLE}=================================================={RESET}")
    print(f"{HACKER_GREEN}{BOLD}    🚀 CBR SMART REDMI FLASHER (OTG SAFE) 🚀    {RESET}")
    print(f"{PURPLE}=================================================={RESET}\n")
    
    print(f"{CYAN}[SECURITY]{RESET} Connecting to Cloud Authorization...")
    live_password = get_cloud_setting('flash_password', 'Powerbycbr')
        
    auth_pass = input(f"{BOLD}{ORANGE}🔑 Enter Flash Authorization Password: {RESET}").strip()
    if auth_pass != live_password and auth_pass != f":{live_password}":
        print(f"\n{RED}[✗] Access Denied: Incorrect Authorization Password!{RESET}")
        send_activity_log("Failed Flash Attempt: Wrong Auth Password")
        time.sleep(2)
        if not IS_WINDOWS: os.system("termux-wake-unlock > /dev/null 2>&1")
        return
        
    print(f"{GREEN}[✓] Access Granted! Loading CBR Flasher Engine...{RESET}")
    send_activity_log("Opened CBR Smart Flasher Engine")
    time.sleep(1)

    rom_dir = "/sdcard/Download" if not IS_WINDOWS else os.path.expanduser("~\\Downloads")
    print(f"\n{CYAN}[SCANNING]{RESET} Searching for ROM Zips & Unzipped Folders in {rom_dir}...")
    
    if not os.path.exists(rom_dir) and not IS_WINDOWS:
        os.system("termux-setup-storage")
        time.sleep(2)
        
    # --- SMART FOLDER SCANNER ---
    rom_archives = glob.glob(f"{rom_dir}/*.tgz") + glob.glob(f"{rom_dir}/*.zip") + glob.glob(f"{rom_dir}/*.tar.gz")
    rom_folders = []
    
    try:
        for item in os.listdir(rom_dir):
            item_path = os.path.join(rom_dir, item)
            if os.path.isdir(item_path):
                if os.path.exists(os.path.join(item_path, "flash_all.sh")) or os.path.exists(os.path.join(item_path, "flash_all.bat")):
                    rom_folders.append(item_path)
                else:
                    for sub in os.listdir(item_path):
                        sub_path = os.path.join(item_path, sub)
                        if os.path.isdir(sub_path):
                            if os.path.exists(os.path.join(sub_path, "flash_all.sh")) or os.path.exists(os.path.join(sub_path, "flash_all.bat")):
                                rom_folders.append(sub_path)
    except: pass
        
    all_roms = list(set(rom_folders)) + rom_archives
    if not all_roms:
        print(f"{ORANGE}[!] No valid ROMs found in {rom_dir}.{RESET}")
        if not IS_WINDOWS: os.system("termux-wake-unlock > /dev/null 2>&1")
        return
        
    print(f"\n{GREEN}--- Found ROM Files ---{RESET}")
    for i, file in enumerate(all_roms):
        print(f" [{i+1}] {BOLD}{CYAN if os.path.isdir(file) else ORANGE}[{'DIR' if os.path.isdir(file) else 'ZIP'}]{RESET} {os.path.basename(file)}")
        
    try:
        sel = int(input(f"\n{BOLD}{ORANGE}👉 Select ROM number to Extract/Flash: {RESET}").strip())
        selected_rom = all_roms[sel-1]
    except: return

    # Check if pre-unzipped
    if os.path.isdir(selected_rom):
        print(f"\n{CYAN}[SMART DETECT]{RESET} Pre-unzipped folder detected! Skipping extraction... 🚀")
        extract_folder = selected_rom
    else:
        extract_folder = os.path.join(rom_dir, "CBR_Extracted_ROM")
        print(f"\n{CYAN}[EXTRACTING]{RESET} Unpacking {os.path.basename(selected_rom)}...")
        try:
            if os.path.exists(extract_folder): shutil.rmtree(extract_folder)
            os.makedirs(extract_folder)
            
            if selected_rom.endswith('.zip'):
                with zipfile.ZipFile(selected_rom, 'r') as zf:
                    infos = zf.infolist()
                    total_size = sum(info.file_size for info in infos)
                    extracted_size = 0
                    for info in infos:
                        target_path = os.path.join(extract_folder, info.filename)
                        if info.is_dir() or info.filename.endswith('/'): os.makedirs(target_path, exist_ok=True); continue
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zf.open(info) as source, open(target_path, 'wb') as target:
                            while True:
                                chunk = source.read(1024 * 1024) 
                                if not chunk: break
                                target.write(chunk)
                                extracted_size += len(chunk)
                                pct = (extracted_size / total_size) * 100 if total_size > 0 else 100
                                sys.stdout.write(f"\r\033[K{ORANGE}>>{RESET} {CYAN}Unpacking:{RESET} {BOLD}{GREEN}{pct:.1f}%{RESET}")
                                sys.stdout.flush()
            else:
                with tarfile.open(selected_rom, 'r:*') as tf:
                    members = tf.getmembers()
                    total_size = sum(m.size for m in members)
                    extracted_size = 0
                    for m in members:
                        target_path = os.path.join(extract_folder, m.name)
                        if m.isdir() or m.name.endswith('/'): os.makedirs(target_path, exist_ok=True); continue
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        f = tf.extractfile(m)
                        if f:
                            with open(target_path, 'wb') as target:
                                while True:
                                    chunk = f.read(1024 * 1024) 
                                    if not chunk: break
                                    target.write(chunk)
                                    extracted_size += len(chunk)
                                    pct = (extracted_size / total_size) * 100 if total_size > 0 else 100
                                    sys.stdout.write(f"\r\033[K{ORANGE}>>{RESET} {CYAN}Unpacking:{RESET} {BOLD}{GREEN}{pct:.1f}%{RESET}")
                                    sys.stdout.flush()
            print(f"\n\n{GREEN}[✓] Extraction Complete!{RESET}")
        except Exception as e:
            print(f"\n\n{RED}[!] Extraction Failed: {e}{RESET}")
            return

    sh_file = None
    for root, dirs, files in os.walk(extract_folder):
        if "flash_all.sh" in files: sh_file = os.path.join(root, "flash_all.sh"); break
        elif "flash_all.bat" in files: sh_file = os.path.join(root, "flash_all.bat"); break
            
    if not sh_file:
        print(f"{RED}[!] Error: 'flash_all.sh' not found in extracted files!{RESET}")
        return

    script_dir = os.path.dirname(sh_file)
    print(f"\n{CYAN}[PRE-CHECK]{RESET} Verifying Device Connection...")
    if not utils.get_device_info(): return
        
    print(f"\n{CYAN}--- HOST DEVICE RAM OPTIMIZATION ---{RESET}")
    print(f"{GREEN} [1]{RESET} Normal Mode (For PC or 6GB+ RAM Phones - High Speed/No CRC Error)")
    print(f"{ORANGE} [2]{RESET} Low RAM Mode (For 3GB/4GB Phones - Slices super.img to prevent crash)")
    ram_choice = input(f"\n{BOLD}{ORANGE}👉 Select Mode: {RESET}").strip()
    use_ram_shield = (ram_choice == '2')

    print(f"\n{CYAN}--- FLASHING OPTIONS ---{RESET}")
    print(f"{GREEN} [1]{RESET} Flash All (Keep Bootloader Unlocked)")
    print(f"{RED} [2]{RESET} Flash All & Lock (Lock Bootloader)")
    lock_choice = input(f"\n{BOLD}{ORANGE}👉 Select Option: {RESET}").strip()

    print(f"\n{HACKER_GREEN}[STARTING CBR FLASH ENGINE]{RESET}")
    send_activity_log(f"Started Flashing ROM: {os.path.basename(selected_rom)}")
    
    with open(sh_file, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()
    fb_bin = utils.get_fastboot_bin()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('rem') or line.startswith('echo'): continue

        if line.startswith('fastboot'):
            cmd = line.replace('`dirname $0`', script_dir).replace('%~dp0', script_dir + '/')
            cmd = cmd.replace('$*', '').replace('%*', '').replace('\\', '/')
            
            is_valid_action = False
            valid_keywords = ['flash', 'erase', 'format', 'boot', 'reboot', 'oem', 'set_active']
            cmd_parts = [p.lower() for p in cmd.split() if p.lower() != 'fastboot' and not p.startswith('-')]
            
            if cmd_parts:
                action = cmd_parts[0]
                if any(action.startswith(vk) for vk in valid_keywords) and '|' not in cmd and '>' not in cmd and 'grep' not in cmd:
                    is_valid_action = True
                    
            if not is_valid_action:
                print(f"{ORANGE}[BYPASS]{RESET} {DIM}Skipping script logic: {line}{RESET}")
                continue
            
            if fb_bin != "fastboot" and cmd.startswith("fastboot "):
                cmd = fb_bin + cmd[8:]

            # 🔥 LOW RAM SHIELD FOR WEAK DEVICES 🔥
            if use_ram_shield and not IS_WINDOWS:
                if "flash super " in cmd.lower() or "flash userdata " in cmd.lower():
                    if "-s" not in cmd.lower():
                        cmd = cmd.replace("flash ", "-S 128M flash ", 1)
                        print(f"{CYAN}[LOW RAM MODE]{RESET} Safe chunking applied for weak Host RAM!")
            
            success = False
            for attempt in range(3):
                print(f"\n{ORANGE}[RUNNING]{RESET} {cmd}")
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, errors='replace')
                
                for out_line in process.stdout:
                    line_lower = out_line.lower()
                    if "error" in line_lower or "failed" in line_lower:
                        if "locked" in line_lower or "not allowed" in line_lower: print(f"{RED}   [DIAGNOSTIC] Bootloader is Locked!{RESET}")
                        elif "anti-rollback" in line_lower: print(f"{RED}   [DIAGNOSTIC] Anti-Rollback triggered!{RESET}")
                        elif "not found" in line_lower and "partition" in line_lower: print(f"{ORANGE}   [DIAGNOSTIC] Partition missing. Skipping.{RESET}")
                        elif "protocol" in line_lower or "timeout" in line_lower: print(f"{RED}   [DIAGNOSTIC] USB Connection Dropped!{RESET}")
                    print(f"{DIM}   >> {out_line.strip()}{RESET}")
                
                process.wait()
                if process.returncode == 0: success = True; break
                else:
                    print(f"{RED}[!] Failed. OTG Retry ({attempt+1}/3)...{RESET}")
                    utils.trigger_otg_popup(force=True)
                    time.sleep(3)
                    
            if not success: print(f"{RED}[!] Skipping partition after 3 failures to prevent brick.{RESET}")
            time.sleep(2)
            try: subprocess.run(f"{fb_bin} devices > /dev/null 2>&1", shell=True, timeout=4)
            except: pass

    if lock_choice == '2':
        print(f"\n{ORANGE}[LOCKING BOOTLOADER]{RESET}")
        subprocess.run(f"{fb_bin} oem lock", shell=True)
        
    print(f"\n{GREEN}[✓] FLASHING COMPLETED SUCCESSFULLY!{RESET}")
    print(f"{CYAN}[*] Rebooting Phone...{RESET}")
    subprocess.run(f"{fb_bin} reboot", shell=True)
    if not IS_WINDOWS: os.system("termux-wake-unlock > /dev/null 2>&1")


# ==========================================
# 🚀 INFINIX FASTBOOTD ENGINE (FROM BACKUP) 🚀
# ==========================================
def _cbr_infinix_native():
    if not IS_WINDOWS: os.system("termux-wake-lock > /dev/null 2>&1")
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{PURPLE}=================================================={RESET}")
    print(f"{HACKER_GREEN}{BOLD}   🚀 CBR INFINIX STOCK ROM FLASHER (FASTBOOTD) 🚀   {RESET}")
    print(f"{PURPLE}=================================================={RESET}\n")
    
    print(f"{CYAN}[SECURITY]{RESET} Connecting to Cloud Authorization...")
    live_password = get_cloud_setting('infinix_password', 'cbr')
        
    auth_pass = input(f"{BOLD}{ORANGE}🔑 Enter Infinix Flash Authorization Password: {RESET}").strip()
    if auth_pass != live_password and auth_pass != f":{live_password}":
        print(f"\n{RED}[✗] Access Denied!{RESET}")
        if not IS_WINDOWS: os.system("termux-wake-unlock > /dev/null 2>&1")
        return
        
    print(f"{GREEN}[✓] Access Granted! Loading CBR Infinix Engine...{RESET}")
    send_activity_log("Opened CBR Infinix Stock ROM Flasher")
    time.sleep(1)

    rom_dir = "/sdcard/Download" if not IS_WINDOWS else os.path.expanduser("~\\Downloads")
    print(f"\n{CYAN}[SCANNING]{RESET} Searching for Infinix ROM Zips & Scatter Folders in {rom_dir}...")
    
    rom_archives = glob.glob(f"{rom_dir}/*.zip") + glob.glob(f"{rom_dir}/*.tgz") + glob.glob(f"{rom_dir}/*.tar.gz")
    rom_folders = []
    
    def is_inf_dir(d_path):
        try:
            for f in os.listdir(d_path):
                if "scatter" in f.lower() or f.lower() == "super.img": return True
        except: pass
        return False

    try:
        for item in os.listdir(rom_dir):
            item_path = os.path.join(rom_dir, item)
            if os.path.isdir(item_path):
                if is_inf_dir(item_path): rom_folders.append(item_path)
                else:
                    for sub in os.listdir(item_path):
                        sub_path = os.path.join(item_path, sub)
                        if os.path.isdir(sub_path) and is_inf_dir(sub_path): rom_folders.append(sub_path)
    except: pass
        
    all_roms = list(set(rom_folders)) + rom_archives
    if not all_roms: return
        
    for i, file in enumerate(all_roms):
        print(f" [{i+1}] {BOLD}{CYAN if os.path.isdir(file) else ORANGE}[{'DIR' if os.path.isdir(file) else 'ZIP'}]{RESET} {os.path.basename(file)}")
        
    try:
        sel = int(input(f"\n{BOLD}{ORANGE}👉 Select ROM number to Extract/Flash: {RESET}").strip())
        selected_rom = all_roms[sel-1]
    except: return

    if os.path.isdir(selected_rom): extract_folder = selected_rom
    else:
        extract_folder = os.path.join(rom_dir, "CBR_Extracted_Infinix_ROM")
        print(f"\n{CYAN}[EXTRACTING]{RESET} Unpacking {os.path.basename(selected_rom)}...")
        try:
            if os.path.exists(extract_folder): shutil.rmtree(extract_folder)
            os.makedirs(extract_folder)
            
            if selected_rom.endswith('.zip'):
                with zipfile.ZipFile(selected_rom, 'r') as zf:
                    for info in zf.infolist():
                        target_path = os.path.join(extract_folder, info.filename)
                        if info.is_dir() or info.filename.endswith('/'): os.makedirs(target_path, exist_ok=True); continue
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zf.open(info) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
            else:
                with tarfile.open(selected_rom, 'r:*') as tf:
                    for m in tf.getmembers():
                        target_path = os.path.join(extract_folder, m.name)
                        if m.isdir() or m.name.endswith('/'): os.makedirs(target_path, exist_ok=True); continue
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        f = tf.extractfile(m)
                        if f:
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(f, target)
        except Exception as e:
            print(f"\n{RED}[!] Extraction Failed: {e}{RESET}")
            return

    rom_img_dir = None
    scatter_found = None
    scatter_full_path = None
    for root, dirs, files in os.walk(extract_folder):
        for f_name in sorted(files):
            if "scatter" in f_name.lower() and f_name.endswith(".txt"):
                scatter_found = f_name; scatter_full_path = os.path.join(root, f_name); rom_img_dir = root; break
        if not scatter_found:
            for f_name in sorted(files):
                if "scatter" in f_name.lower() and f_name.endswith(".xml"):
                    scatter_found = f_name; scatter_full_path = os.path.join(root, f_name); rom_img_dir = root; break
        if not rom_img_dir:
            for f_name in files:
                if f_name.lower() == "super.img": rom_img_dir = root; break
        if rom_img_dir and scatter_found: break

    if not rom_img_dir: return

    risky_blacklist = {"preloader", "pgpt", "nvram", "nvdata", "nvcfg", "protect1", "protect2", "persist", "seccfg", "proinfo", "frp", "metadata"}
    vbmeta_base_names = {"vbmeta", "vbmeta_system", "vbmeta_vendor"}
    baseline_ab_partitions = [("boot", "boot.img"), ("init_boot", "init_boot.img"), ("dtbo", "dtbo.img"), ("lk", "lk.img")]
    
    scatter_ab_map = {b: f for b, f in baseline_ab_partitions}
    scatter_single_map = {"super": "super.img", "userdata": "userdata.img"}
    scatter_vbmeta_map = {"vbmeta": "vbmeta.img", "vbmeta_system": "vbmeta_system.img", "vbmeta_vendor": "vbmeta_vendor.img"}

    if scatter_full_path and os.path.exists(scatter_full_path):
        print(f"\n{CYAN}[SCATTER PARSER]{RESET} Analyzing {scatter_found}...")
        try:
            with open(scatter_full_path, 'r', encoding='utf-8', errors='ignore') as sf: content = sf.read()
            parsed_entries = []
            if scatter_full_path.endswith(".txt"):
                blocks = content.split("partition_index:")
                for blk in blocks[1:]:
                    p_name_m = re.search(r"partition_name:\s*([^\s\r\n]+)", blk)
                    f_name_m = re.search(r"file_name:\s*([^\s\r\n]+)", blk)
                    is_dl_m = re.search(r"is_download:\s*([^\s\r\n]+)", blk)
                    if p_name_m and f_name_m:
                        p_name = p_name_m.group(1).strip().strip('"\''); f_name = f_name_m.group(1).strip().strip('"\'')
                        is_dl = is_dl_m.group(1).strip().lower() if is_dl_m else "true"
                        if is_dl == "true" and f_name.lower() != "none": parsed_entries.append((p_name, f_name))
            
            for p_name, f_name in parsed_entries:
                p_low = p_name.lower()
                base_p = p_low[:-2] if (p_low.endswith("_a") or p_low.endswith("_b")) else p_low
                if p_low in risky_blacklist or base_p in risky_blacklist or "preloader" in p_low: continue
                if base_p in vbmeta_base_names or p_low.startswith("vbmeta"): scatter_vbmeta_map[base_p] = f_name
                elif base_p in ("super", "userdata"): scatter_single_map[base_p] = f_name
                else: scatter_ab_map[base_p] = f_name
        except: pass

    print(f"\n{CYAN}--- HOST DEVICE RAM OPTIMIZATION ---{RESET}")
    print(f"{GREEN} [1]{RESET} Normal Mode (Flash large super.img natively)")
    print(f"{ORANGE} [2]{RESET} Low RAM Mode (Use 64M Chunks to prevent crash)")
    ram_opt = input(f"{BOLD}{ORANGE}👉 Select Mode: {RESET}").strip()
    super_flags = "-S 64M" if ram_opt == '2' else ""

    print(f"\n{CYAN}[PRE-CHECK]{RESET} Checking Device...")
    if not utils.get_device_info(): return

    fb_bin = utils.get_fastboot_bin()
    total_flash_steps = 12 + (len(scatter_ab_map) * 2) + 1 + (len(scatter_vbmeta_map) * 2) + 1
    current_flash_step = 0
    user_aborted_flash = False

    def wait_for_fastboot_device(mode_label):
        nonlocal fb_bin, user_aborted_flash
        utils.GRANTED_USB_DEVS.clear()
        print(f"\n{CYAN}[*] Waiting for {mode_label}...{RESET}")
        time.sleep(4)
        while True:
            utils.trigger_otg_popup(silent=False, force=True)
            fb_bin = utils.get_fastboot_bin()
            dev_out = utils.run_usb_fastboot_probe(fb_bin, ["devices"], timeout_sec=4)
            if dev_out and "permission" not in dev_out.lower(): return True
            if utils.ACTIVE_USB_DEV and utils.ACTIVE_USB_DEV in utils.GRANTED_USB_DEVS: return True

            print(f"\n{ORANGE}{BOLD} ⚠️  DEVICE DISCONNECTED ⚠️{RESET}")
            print(f"{GREEN} [1]{RESET} 🔄 Try Connect")
            print(f"{RED} [2]{RESET} ❌ Exit")
            rec_choice = input(f"\n{BOLD}{ORANGE}👉 Select Option: {RESET}").strip()
            
            if rec_choice == '2': user_aborted_flash = True; return False
            else:
                utils.GRANTED_USB_DEVS.clear()
                for retry_i in range(1, 4):
                    utils.trigger_otg_popup(silent=False, force=True)
                    if utils.ACTIVE_USB_DEV and utils.ACTIVE_USB_DEV in utils.GRANTED_USB_DEVS: return True
                    time.sleep(2)

    def is_device_in_fastbootd():
        nonlocal fb_bin
        utils.trigger_otg_popup(silent=True)
        fb_bin = utils.get_fastboot_bin()
        comb = utils.run_usb_fastboot_probe(fb_bin, ["getvar", "is-userspace"], timeout_sec=4).lower()
        return "is-userspace: yes" in comb

    def execute_single_fastboot_cmd(cmd_str, step_label, allow_skip=False, is_reboot_cmd=False):
        nonlocal fb_bin, current_flash_step, user_aborted_flash
        if user_aborted_flash: return False
        current_flash_step += 1
        success = False

        while not user_aborted_flash:
            for attempt in range(3):
                utils.trigger_otg_popup(silent=True)
                fb_bin = utils.get_fastboot_bin()
                run_cmd = cmd_str
                if fb_bin != "fastboot" and run_cmd.startswith("fastboot "): run_cmd = fb_bin + run_cmd[8:]
                print(f"\n{ORANGE}[{step_label} | RUNNING]{RESET} {run_cmd}")
                
                process = subprocess.Popen(run_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, errors='replace')
                saw_waiting_for_device = False
                reboot_okay_seen = False

                for out_line in process.stdout:
                    line_lower = out_line.lower()
                    print(f"{DIM}   >> {out_line.strip()}{RESET}")
                    if "waiting for any device" in line_lower or "< waiting for" in line_lower or "no such device" in line_lower:
                        saw_waiting_for_device = True; process.kill(); break
                    if is_reboot_cmd and "okay" in line_lower:
                        reboot_okay_seen = True; process.kill(); break
                
                try: process.wait(timeout=3)
                except: process.kill()

                if is_reboot_cmd and (reboot_okay_seen or saw_waiting_for_device or process.returncode == 0): success = True; break
                
                if process.returncode != 0 and not saw_waiting_for_device and utils.ACTIVE_USB_DEV and shutil.which("termux-usb") is not None:
                    bridge_proc = subprocess.Popen(["termux-usb", "-e", cmd_str, utils.ACTIVE_USB_DEV], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, errors='replace')
                    for b_line in bridge_proc.stdout:
                        if "waiting for any device" in b_line.lower(): saw_waiting_for_device = True; bridge_proc.kill(); break
                    bridge_proc.wait()
                    if bridge_proc.returncode == 0 and not saw_waiting_for_device: process.returncode = 0

                if process.returncode == 0 and not saw_waiting_for_device: success = True; break
                else:
                    if allow_skip and attempt == 0 and not saw_waiting_for_device: success = True; break
                    if saw_waiting_for_device:
                        if not wait_for_fastboot_device("Active Fastboot Mode"): return False
                        continue
                    time.sleep(2)
            if success: break
            else:
                if not wait_for_fastboot_device("Fastboot Mode"): return False
        return success

    def flash_partition_file(part_name, img_filename, step_label, extra_flags=""):
        if user_aborted_flash: return
        img_path = os.path.join(rom_img_dir, img_filename)
        if not os.path.exists(img_path): return
        flag_str = f"{extra_flags} " if extra_flags else ""
        execute_single_fastboot_cmd(f'fastboot {flag_str}flash {part_name} "{img_path}"', step_label)

    print(f"\n{CYAN}{BOLD}>>> STAGE 1: FASTBOOTD MODE OPERATIONS <<<{RESET}")
    if not is_device_in_fastbootd():
        execute_single_fastboot_cmd("fastboot reboot fastboot", "STEP 2-A", is_reboot_cmd=True)
        if not wait_for_fastboot_device("FastbootD Mode") or user_aborted_flash: return

    for l_part in ["product", "system", "system_ext", "system_ext_a", "system_ext_b", "product_a", "product_b"]:
        execute_single_fastboot_cmd(f"fastboot delete-logical-partition {l_part}", "CLEANUP", allow_skip=True)

    # Flash super.img based on RAM Choice
    flash_partition_file("super", scatter_single_map.get("super", "super.img"), "FLASH-SUPER", extra_flags=super_flags)
    execute_single_fastboot_cmd("fastboot -w", "FORMAT-USERDATA", allow_skip=True)

    if user_aborted_flash: return

    print(f"\n{CYAN}{BOLD}>>> STAGE 2: BOOTLOADER MODE FLASHING <<<{RESET}")
    execute_single_fastboot_cmd("fastboot reboot bootloader", "BOOTLOADER-SWITCH", is_reboot_cmd=True)
    if not wait_for_fastboot_device("Bootloader Mode") or user_aborted_flash: return

    for base_part, img_file in scatter_ab_map.items():
        if user_aborted_flash: break
        flash_partition_file(f"{base_part}_a", img_file, f"PART-{base_part}A")
        flash_partition_file(f"{base_part}_b", img_file, f"PART-{base_part}B")

    if not user_aborted_flash:
        flash_partition_file("userdata", scatter_single_map.get("userdata", "userdata.img"), "STEP-USERDATA")

    if not user_aborted_flash:
        print(f"\n{CYAN}{BOLD}>>> STAGE 3: VBMETA DISABLE <<<{RESET}")
        vbmeta_flags = "--disable-verity --disable-verification"
        for vb_base, vb_file in scatter_vbmeta_map.items():
            if user_aborted_flash: break
            flash_partition_file(f"{vb_base}_a", vb_file, f"{vb_base}-A", extra_flags=vbmeta_flags)
            flash_partition_file(f"{vb_base}_b", vb_file, f"{vb_base}-B", extra_flags=vbmeta_flags)

    execute_single_fastboot_cmd("fastboot reboot recovery", "FINAL-BOOT", allow_skip=True, is_reboot_cmd=True)
    print(f"\n{GREEN}{BOLD}[✓] INFINIX STOCK ROM FLASHING COMPLETED SUCCESSFULLY!{RESET}")
    if not IS_WINDOWS: os.system("termux-wake-unlock > /dev/null 2>&1")
