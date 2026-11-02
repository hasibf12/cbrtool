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
    CYAN, ORANGE, GREEN, RED, PURPLE, HACKER_GREEN, RESET, BOLD, DIM,
    get_cloud_setting, IS_WINDOWS
)
from core.utils import (
    get_device_info, wait_and_connect_fastboot, get_fastboot_bin,
    trigger_otg_popup
)
from core.auth import send_activity_log

def extract_safe_zip(zip_path, extract_folder):
    print(f"\n{CYAN}[EXTRACTING]{RESET} Unpacking {os.path.basename(zip_path)}...")
    print(f"{DIM}Please wait, calculating total size...{RESET}\n")
    try:
        if os.path.exists(extract_folder):
            shutil.rmtree(extract_folder)
        os.makedirs(extract_folder)
        
        if zip_path.endswith('.zip'):
            with zipfile.ZipFile(zip_path, 'r') as zf:
                infos = zf.infolist()
                total_size = sum(info.file_size for info in infos)
                extracted_size = 0
                for info in infos:
                    target_path = os.path.join(extract_folder, info.filename)
                    if info.is_dir() or info.filename.endswith('/'):
                        os.makedirs(target_path, exist_ok=True)
                        continue
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    if os.path.isdir(target_path): continue
                    
                    with zf.open(info) as source, open(target_path, 'wb') as target:
                        while True:
                            chunk = source.read(1024 * 1024) 
                            if not chunk: break
                            target.write(chunk)
                            extracted_size += len(chunk)
                            percent = (extracted_size / total_size) * 100 if total_size > 0 else 100
                            mb_ex = extracted_size / (1024 * 1024)
                            mb_tot = total_size / (1024 * 1024)
                            sys.stdout.write(f"\r\033[K{ORANGE}>>{RESET} {CYAN}Unpacking:{RESET} {BOLD}{GREEN}{percent:.1f}%{RESET} | {mb_ex:.1f} MB / {mb_tot:.1f} MB")
                            sys.stdout.flush()
        else:
            with tarfile.open(zip_path, 'r:*') as tf:
                members = tf.getmembers()
                total_size = sum(m.size for m in members)
                extracted_size = 0
                for m in members:
                    target_path = os.path.join(extract_folder, m.name)
                    if m.isdir() or m.name.endswith('/'):
                        os.makedirs(target_path, exist_ok=True)
                        continue
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    if os.path.isdir(target_path): continue
                    
                    f = tf.extractfile(m)
                    if f:
                        with open(target_path, 'wb') as target:
                            while True:
                                chunk = f.read(1024 * 1024) 
                                if not chunk: break
                                target.write(chunk)
                                extracted_size += len(chunk)
                                percent = (extracted_size / total_size) * 100 if total_size > 0 else 100
                                mb_ex = extracted_size / (1024 * 1024)
                                mb_tot = total_size / (1024 * 1024)
                                sys.stdout.write(f"\r\033[K{ORANGE}>>{RESET} {CYAN}Unpacking:{RESET} {BOLD}{GREEN}{percent:.1f}%{RESET} | {mb_ex:.1f} MB / {mb_tot:.1f} MB")
                                sys.stdout.flush()
        print(f"\n\n{GREEN}[✓] Extraction Complete!{RESET}")
        return True
    except Exception as e:
        print(f"\n\n{RED}[!] Extraction Failed: {e}{RESET}")
        return False

def cbr_smart_scanner(mode="all"):
    print(f"\n{CYAN}[SCANNING]{RESET} Deep Scanning for ROMs in Folders...")
    search_paths = [os.path.expanduser("~\\Downloads"), os.path.expanduser("~\\Desktop"), os.getcwd()] if IS_WINDOWS else ["/sdcard/Download", os.getcwd()]
    valid_roms = []
    
    if not IS_WINDOWS and not os.path.exists("/sdcard/Download"):
        print(f"{ORANGE}[*] Requesting storage access...{RESET}")
        os.system("termux-setup-storage")
        time.sleep(2)
        
    for s_path in search_paths:
        if not os.path.exists(s_path): continue
        valid_roms.extend(glob.glob(f"{s_path}/*.zip") + glob.glob(f"{s_path}/*.tgz") + glob.glob(f"{s_path}/*.tar.gz"))
        try:
            for root, dirs, files in os.walk(s_path):
                if "CBR_Extracted" in root: continue
                depth = root[len(s_path):].count(os.sep)
                if depth > 4: del dirs[:]; continue
                
                is_valid = False
                for f in files:
                    f_low = f.lower()
                    if mode == "mtk" and "scatter" in f_low and f_low.endswith(".txt"): is_valid = True; break
                    elif mode == "fastboot" and (f_low == "flash_all.sh" or f_low == "flash_all.bat"): is_valid = True; break
                    elif mode == "all" and ("scatter" in f_low or f_low == "flash_all.sh" or f_low == "flash_all.bat"): is_valid = True; break
                if is_valid and root not in valid_roms: valid_roms.append(root)
        except: pass
    return list(set(valid_roms))

def cbr_smart_flasher(brand="redmi"):
    import shlex
    if not IS_WINDOWS: os.system("termux-wake-lock > /dev/null 2>&1")
    os.system('cls' if os.name == 'nt' else 'clear')
    
    brand_name = "REDMI NATIVE" if brand == "redmi" else "INFINIX FASTBOOTD"
    print(f"{PURPLE}=================================================={RESET}")
    print(f"{HACKER_GREEN}{BOLD}    🚀 CBR SMART {brand_name} FLASHER 🚀    {RESET}")
    print(f"{PURPLE}=================================================={RESET}\n")
    
    pass_key = 'flash_password' if brand == "redmi" else 'infinix_password'
    live_password = get_cloud_setting(pass_key, 'Powerbycbr' if brand=="redmi" else 'cbr')
    auth_pass = input(f"{BOLD}{ORANGE}🔑 Enter Authorization Password: {RESET}").strip()
    
    if auth_pass != live_password and auth_pass != f":{live_password}":
        print(f"\n{RED}[✗] Access Denied!{RESET}"); time.sleep(2); return
        
    print(f"{GREEN}[✓] Access Granted! Loading Engine...{RESET}"); time.sleep(1)

    all_roms = cbr_smart_scanner(mode="fastboot" if brand == "redmi" else "mtk")
    if not all_roms: 
        print(f"\n{RED}[!] No Valid ROMs Found.{RESET}")
        input(f"\n{PURPLE}Press Enter...{RESET}")
        return
        
    for i, file in enumerate(all_roms):
        print(f" [{i+1}] {'[DIR]' if os.path.isdir(file) else '[ZIP]'} {os.path.basename(file)}")
        
    try:
        sel = int(input(f"\n{BOLD}{ORANGE}👉 Select ROM number: {RESET}").strip())
        selected_rom = all_roms[sel-1]
    except: return

    extract_folder = selected_rom
    if not os.path.isdir(selected_rom):
        extract_folder = os.path.join(os.path.dirname(selected_rom), "CBR_Extracted_ROM")
        if not extract_safe_zip(selected_rom, extract_folder): 
            input(f"\n{PURPLE}Press Enter...{RESET}")
            return

    if brand == "redmi":
        sh_file = None
        for root, dirs, files in os.walk(extract_folder):
            if "flash_all.sh" in files:
                sh_file = os.path.join(root, "flash_all.sh")
                break
            elif "flash_all.bat" in files:
                sh_file = os.path.join(root, "flash_all.bat")
                break
                
        if not sh_file: 
            print(f"{RED}[!] 'flash_all' script not found inside extracted folder!{RESET}")
            input(f"\n{PURPLE}Press Enter...{RESET}")
            return
            
        script_dir = os.path.dirname(sh_file)
        if not wait_and_connect_fastboot(): return
        get_device_info()
        
        print(f"\n{CYAN}--- FLASHING OPTIONS ---{RESET}")
        print(f"{GREEN} [1]{RESET} Flash All (Keep Unlocked)  {RED}[2]{RESET} Flash All & Lock")
        lock_choice = input(f"{BOLD}{ORANGE}👉 Select Option: {RESET}").strip()

        print(f"\n{HACKER_GREEN}[STARTING CBR FLASH ENGINE]{RESET}")
        fb_bin = get_fastboot_bin()
        with open(sh_file, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('rem') or line.startswith('echo'): continue
            
            if line.startswith('fastboot') or line.lower().startswith('fastboot'):
                cmd = line.replace('`dirname $0`', shlex.quote(script_dir)).replace('%~dp0', shlex.quote(script_dir) + os.sep)
                cmd = cmd.replace('$*', '').replace('%*', '')
                
                is_valid_action = False
                valid_keywords = ['flash', 'erase', 'format', 'boot', 'reboot', 'oem', 'set_active']
                cmd_parts = [p.lower() for p in cmd.split() if p.lower() != 'fastboot' and not p.startswith('-')]
                
                if cmd_parts:
                    action = cmd_parts[0]
                    if any(action.startswith(vk) for vk in valid_keywords) and '|' not in cmd and '>' not in cmd and 'grep' not in cmd:
                        is_valid_action = True
                        
                if not is_valid_action:
                    print(f"{ORANGE}[BYPASS]{RESET} {DIM}Skipping script logic/check: {line}{RESET}")
                    continue
                
                if fb_bin != "fastboot" and cmd.lower().startswith("fastboot "): cmd = fb_bin + cmd[8:]
                
                success = False
                for attempt in range(3):
                    print(f"\n{ORANGE}[RUNNING]{RESET} {cmd}")
                    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, errors='replace')
                    saw_waiting = False
                    for out_line in process.stdout: 
                        print(f"{DIM}   >> {out_line.strip()}{RESET}")
                        if "waiting for" in out_line.lower() or "no such device" in out_line.lower():
                            saw_waiting = True
                    process.wait()
                    
                    if process.returncode == 0 and not saw_waiting:
                        success = True
                        break
                    else:
                        print(f"{RED}[!] Command failed or device disconnected. Reconnecting ({attempt+1}/3)...{RESET}")
                        trigger_otg_popup(force=True)
                        time.sleep(3)
                        
                if not success:
                    print(f"{RED}[!] Critical Failure at step: {cmd}. Stopping to prevent brick.{RESET}")
                    break
                    
                if "reboot" in cmd.lower() and "bootloader" in cmd.lower():
                    time.sleep(5)
                    wait_and_connect_fastboot()

        if lock_choice == '2': 
            print(f"\n{ORANGE}[LOCKING BOOTLOADER]{RESET}")
            subprocess.run([fb_bin, "oem", "lock"])
            
        print(f"\n{GREEN}[✓] COMPLETED! Rebooting...{RESET}")
        subprocess.run([fb_bin, "reboot"])
        input(f"\n{PURPLE}Press Enter...{RESET}")

    else:
        # INFINIX FASTBOOTD LOGIC
        scatter_found, scatter_full_path, rom_img_dir = None, None, None
        for root, dirs, files in os.walk(extract_folder):
            for f in files:
                if "scatter" in f.lower() and (f.endswith(".txt") or f.endswith(".xml")):
                    scatter_found, scatter_full_path, rom_img_dir = f, os.path.join(root, f), root
                    break
            if scatter_found: break
        if not rom_img_dir: 
            print(f"{RED}[!] Scatter not found!{RESET}"); input(f"\n{PURPLE}Press Enter...{RESET}"); return

        scatter_ab_map, scatter_single_map, scatter_vbmeta_map = {}, {"super": "super.img", "userdata": "userdata.img"}, {}
        if scatter_full_path and os.path.exists(scatter_full_path):
            try:
                with open(scatter_full_path, 'r', encoding='utf-8', errors='ignore') as sf: content = sf.read()
                for blk in content.split("partition_index:")[1:]:
                    p_name_m = re.search(r"partition_name:\s*([^\s\r\n]+)", blk)
                    f_name_m = re.search(r"file_name:\s*([^\s\r\n]+)", blk)
                    if p_name_m and f_name_m:
                        p_name = p_name_m.group(1).strip().strip('"\'').lower()
                        f_name = f_name_m.group(1).strip().strip('"\'')
                        if f_name.lower() != "none":
                            base_p = p_name[:-2] if (p_name.endswith("_a") or p_name.endswith("_b")) else p_name
                            if base_p in ["nvcfg", "seccfg", "proinfo", "protect1", "protect2", "nvdata", "nvram"]: continue
                            
                            if base_p in ["super", "userdata"]: scatter_single_map[base_p] = f_name
                            elif base_p in ["vbmeta", "vbmeta_system", "vbmeta_vendor"]: scatter_vbmeta_map[base_p] = f_name
                            elif base_p not in ["preloader", "pgpt"]: scatter_ab_map[base_p] = f_name
            except: pass

        if not wait_and_connect_fastboot(): return
        get_device_info()
        
        def execute_cmd(cmd_str, is_reboot=False):
            fb_bin = get_fastboot_bin()
            if fb_bin != "fastboot" and cmd_str.startswith("fastboot "): cmd_str = fb_bin + cmd_str[8:]
            print(f"\n{ORANGE}[RUNNING]{RESET} {cmd_str}")
            p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout: print(f"{DIM}   >> {line.strip()}{RESET}")
            p.wait()
            if is_reboot:
                time.sleep(5)
                wait_and_connect_fastboot()

        print(f"\n{CYAN}>>> FASTBOOTD OPERATIONS <<<{RESET}")
        execute_cmd("fastboot reboot fastboot", is_reboot=True)
        for part in ["product", "system", "system_ext", "product_a", "product_b"]: execute_cmd(f"fastboot delete-logical-partition {part}")
        
        import shlex
        super_path = shlex.quote(os.path.join(rom_img_dir, scatter_single_map.get("super", "super.img")))
        execute_cmd(f'fastboot {"-S 64M " if not IS_WINDOWS else ""}flash super {super_path}')
        execute_cmd("fastboot -w")
        
        print(f"\n{CYAN}>>> BOOTLOADER FLASHING <<<{RESET}")
        execute_cmd("fastboot reboot bootloader", is_reboot=True)
        for b_part, f_name in scatter_ab_map.items():
            img_path = shlex.quote(os.path.join(rom_img_dir, f_name))
            execute_cmd(f'fastboot flash {b_part}_a {img_path}')
            execute_cmd(f'fastboot flash {b_part}_b {img_path}')
        
        user_path = shlex.quote(os.path.join(rom_img_dir, scatter_single_map.get("userdata", "userdata.img")))
        execute_cmd(f'fastboot flash userdata {user_path}')
        
        print(f"\n{CYAN}>>> VBMETA DISABLE <<<{RESET}")
        for v_part, f_name in scatter_vbmeta_map.items():
            vb_path = shlex.quote(os.path.join(rom_img_dir, f_name))
            execute_cmd(f'fastboot --disable-verity --disable-verification flash {v_part}_a {vb_path}')
            execute_cmd(f'fastboot --disable-verity --disable-verification flash {v_part}_b {vb_path}')
            
        execute_cmd("fastboot reboot recovery")
        print(f"\n{GREEN}[✓] INFINIX FLASHING COMPLETED!{RESET}")
        input(f"\n{PURPLE}Press Enter...{RESET}")
