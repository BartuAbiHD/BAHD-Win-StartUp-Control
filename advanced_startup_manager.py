#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Açılış Programları Yönetici - Web UI Versiyonu (PyWebView)
"""

import webview
import winreg
import os
import subprocess
import json
import time
from typing import Dict
import psutil
import urllib.parse
import urllib.request
import webbrowser
import logging
import socket
from logging.handlers import RotatingFileHandler

# Setup logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'startup_control.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_path, maxBytes=1024*1024, backupCount=2),
        logging.StreamHandler()
    ]
)

try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

class StartupApi:
    VERSION = "1.0.0"
    
    def __init__(self):
        self.window = None
        self.startup_programs = {}
        logging.info("StartupApi initialized")

    def set_window(self, window):
        self.window = window

    def extract_file_path(self, program_path: str) -> str:
        if not program_path:
            return ""
        file_path = program_path.strip()
        if file_path.startswith('"') and '"' in file_path[1:]:
            end_quote = file_path.find('"', 1)
            return file_path[1:end_quote]
        else:
            import re
            match = re.match(r'^(.*?\.(?:exe|com|bat|cmd|msi|scr))\s*', file_path, re.IGNORECASE)
            if match:
                return match.group(1)
            parts = file_path.split()
            if parts:
                return parts[0]
            return file_path

    def get_system_impact(self, program_path: str) -> str:
        try:
            file_path = self.extract_file_path(program_path)
            if not os.path.exists(file_path):
                return "Bilinmiyor"
            file_size = os.path.getsize(file_path)
            if file_size < 1024 * 1024:
                return "Düşük"
            elif file_size < 10 * 1024 * 1024:
                return "Orta"
            else:
                return "Yüksek"
        except:
            return "Bilinmiyor"

    def resolve_shortcut(self, lnk_path: str):
        try:
            if win32com is None or pythoncom is None:
                return None, None
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            target_path = shortcut.Targetpath
            arguments = shortcut.Arguments
            pythoncom.CoUninitialize()
            if target_path and os.path.exists(target_path):
                return target_path, arguments
            return None, None
        except Exception:
            try:
                if pythoncom is not None:
                    pythoncom.CoUninitialize()
            except: pass
            return None, None

    def add_folder_program(self, startup_programs: dict, filename: str, file_path: str, base_folder: str, location_name: str, status: str):
        try:
            program_name = os.path.splitext(filename)[0]
            if filename.lower().endswith('.lnk'):
                target_path, arguments = self.resolve_shortcut(file_path)
                if target_path:
                    display_path = f"{target_path} {arguments}" if arguments else target_path
                else:
                    display_path = f"Kısayol: {filename}"
                    target_path = file_path
            else:
                target_path = file_path
                display_path = file_path
            
            original_name = program_name
            counter = 1
            while program_name in startup_programs:
                program_name = f"{original_name} ({counter})"
                counter += 1
                
            startup_programs[program_name] = {
                'path': display_path,
                'registry_key': None,
                'registry_path': base_folder,
                'status': status,
                'location': location_name,
                'impact': self.get_system_impact(target_path),
                'is_folder_based': True,
                'file_path': file_path
            }
        except Exception:
            pass

    def scan_startup_folders(self, startup_programs: dict, startup_folders: list):
        for folder_path, location_name in startup_folders:
            try:
                if not os.path.exists(folder_path):
                    continue
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if filename.lower().endswith(('.lnk', '.exe', '.bat', '.com', '.cmd', '.pif', '.url')):
                        self.add_folder_program(startup_programs, filename, file_path, folder_path, location_name, 'Etkin')
                
                old_disabled = os.path.join(folder_path, "Disabled")
                disabled_folder = os.path.join(os.path.dirname(folder_path), "Startup_Disabled")
                
                if os.path.exists(old_disabled):
                    try:
                        if not os.path.exists(disabled_folder):
                            os.makedirs(disabled_folder)
                        for filename in os.listdir(old_disabled):
                            os.rename(os.path.join(old_disabled, filename), os.path.join(disabled_folder, filename))
                        os.rmdir(old_disabled)
                    except Exception: pass
                
                if os.path.exists(disabled_folder):
                    for filename in os.listdir(disabled_folder):
                        file_path = os.path.join(disabled_folder, filename)
                        if filename.lower().endswith(('.lnk', '.exe', '.bat', '.com', '.cmd', '.pif', '.url')):
                            self.add_folder_program(startup_programs, filename, file_path, folder_path, f"{location_name} (Devre Dışı)", 'Devre Dışı')
            except Exception:
                continue

    def get_programs(self):
        """Returns dict of all startup programs."""
        startup_programs = {}
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM\\WOW6432Node\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\WOW6432Node\\RunOnce"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", "HKCU\\Policies\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", "HKLM\\Policies\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunServices", "HKLM\\RunServices"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunServicesOnce", "HKLM\\RunServicesOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SafeBoot", "HKLM\\SafeBoot"),
        ]
        
        for hkey, subkey_path, location_name in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, reg_type = winreg.EnumValue(key, i)
                            if not name or not name.strip() or not value or not value.strip():
                                i += 1; continue
                            if name.lower() in ['(default)', '(varsayılan)', ''] or len(name.strip()) == 0:
                                i += 1; continue
                            startup_programs[name] = {
                                'path': value, 'registry_key': hkey, 'registry_path': subkey_path,
                                'status': 'Etkin', 'location': location_name, 'impact': self.get_system_impact(value)
                            }
                            i += 1
                        except WindowsError: break
            except Exception: continue
        
        startup_folders = [
            (os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"), "Startup Folder (User)"),
            (r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup", "Startup Folder (All Users)")
        ]
        self.scan_startup_folders(startup_programs, startup_folders)
        
        backup_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\StartupBackup\Run", "HKCU\\Run (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\StartupBackup\Run", "HKLM\\Run (Backup)"),
            (winreg.HKEY_CURRENT_USER, r"Software\StartupBackup\RunOnce", "HKCU\\RunOnce (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\StartupBackup\RunOnce", "HKLM\\RunOnce (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\StartupBackup\Run", "HKLM\\WOW6432Node\\Run (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\StartupBackup\RunOnce", "HKLM\\WOW6432Node\\RunOnce (Backup)"),
            (winreg.HKEY_CURRENT_USER, r"Software\StartupBackup\Policies\Explorer\Run", "HKCU\\Policies\\Run (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\StartupBackup\Policies\Explorer\Run", "HKLM\\Policies\\Run (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\StartupBackup\RunServices", "HKLM\\RunServices (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\StartupBackup\RunServicesOnce", "HKLM\\RunServicesOnce (Backup)"),
            (winreg.HKEY_LOCAL_MACHINE, r"StartupBackup\SafeBoot", "HKLM\\SafeBoot (Backup)"),
        ]
        
        for hkey, subkey_path, location_name in backup_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, reg_type = winreg.EnumValue(key, i)
                            if not name or not name.strip() or not value or not value.strip():
                                i += 1; continue
                            if name.lower() in ['(default)', '(varsayılan)', ''] or len(name.strip()) == 0:
                                i += 1; continue
                            if name not in startup_programs:
                                startup_programs[name] = {
                                    'path': value, 'registry_key': hkey, 'registry_path': subkey_path,
                                    'status': 'Devre Dışı', 'location': location_name, 'impact': self.get_system_impact(value),
                                    'is_backup': True
                                }
                            i += 1
                        except WindowsError: break
            except Exception: continue
        
        try:
            approved_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", "HKCU\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", "HKLM\\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\RunOnce", "HKCU\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\RunOnce", "HKLM\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", "HKLM\\WOW6432Node\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\RunOnce", "HKLM\\WOW6432Node\\RunOnce")
            ]
            for hkey, subkey_path, location_base in approved_paths:
                try:
                    with winreg.OpenKey(hkey, subkey_path) as key:
                        i = 0
                        while True:
                            try:
                                name, value, reg_type = winreg.EnumValue(key, i)
                                if not name or not name.strip() or name.lower() in ['(default)', '(varsayılan)', '']:
                                    i += 1; continue
                                if len(value) >= 1:
                                    status_byte = value[0]
                                    if name in startup_programs:
                                        if not startup_programs[name].get('is_backup') and status_byte == 0x03:
                                            startup_programs[name]['status'] = 'Task Manager Devre Dışı'
                                            startup_programs[name]['is_disabled_by_taskmanager'] = True
                                    elif status_byte == 0x03:
                                        startup_programs[name] = {
                                            'path': 'Bilinmiyor (Task Manager devre dışı)', 'registry_key': hkey,
                                            'registry_path': subkey_path.replace('StartupApproved\\', ''),
                                            'status': 'Task Manager Devre Dışı', 'location': location_base,
                                            'impact': 'Bilinmiyor', 'is_disabled_by_taskmanager': True
                                        }
                                i += 1
                            except WindowsError: break
                except Exception: continue
        except Exception: pass
        
        self.startup_programs = startup_programs
        return startup_programs

    def get_file_info(self, path):
        file_path = self.extract_file_path(path)
        details = f"> Dosya Yolu:\n{file_path}\n\n"
        if os.path.exists(file_path):
            try:
                stat = os.stat(file_path)
                size_mb = stat.st_size / (1024*1024)
                details += f"> Boyut: {size_mb:.2f} MB\n"
                details += f"> Oluşturma: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_ctime))}\n"
                details += f"> Değiştirme: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))}\n"
                details += "\n> Dosya mevcut ve erişilebilir.\n"
            except Exception as e:
                details += f"Hata: {str(e)}\n"
        else:
            details += "UYARI: DOSYA BULUNAMADI VEYA ERİŞİLEMEZ!\n"
        return details

    def disable_program(self, name):
        program_info = self.startup_programs.get(name)
        if not program_info: return {"success": False, "error": "Program bilgileri bulunamadı."}
        try:
            if program_info.get('is_folder_based'):
                original_path = program_info['file_path']
                folder_path = os.path.dirname(original_path)
                disabled_folder = os.path.join(os.path.dirname(folder_path), "Startup_Disabled")
                if not os.path.exists(disabled_folder): os.makedirs(disabled_folder)
                filename = os.path.basename(original_path)
                new_path = os.path.join(disabled_folder, filename)
                os.rename(original_path, new_path)
            else:
                if 'SafeBoot' in program_info['registry_path']:
                    backup_key_path = program_info['registry_path'].replace('SYSTEM\\CurrentControlSet\\Control\\', 'StartupBackup\\')
                else:
                    backup_key_path = program_info['registry_path'].replace('Microsoft\\Windows\\CurrentVersion\\', 'StartupBackup\\')
                with winreg.CreateKey(program_info['registry_key'], backup_key_path) as backup_key:
                    winreg.SetValueEx(backup_key, name, 0, winreg.REG_SZ, program_info['path'])
                with winreg.OpenKey(program_info['registry_key'], program_info['registry_path'], 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def enable_program(self, name):
        program_info = self.startup_programs.get(name)
        if not program_info: return {"success": False, "error": "Program bilgileri bulunamadı."}
        try:
            if program_info.get('is_folder_based') and program_info['status'] == 'Devre Dışı':
                original_path = program_info['file_path']
                base_folder = program_info['registry_path']
                filename = os.path.basename(original_path)
                new_path = os.path.join(base_folder, filename)
                if os.path.exists(new_path):
                    return {"success": False, "error": "Dosya zaten mevcut."}
                os.rename(original_path, new_path)
            elif program_info.get('is_backup') and program_info['status'] == 'Devre Dışı':
                if 'SafeBoot' in program_info['registry_path']:
                    original_path = program_info['registry_path'].replace('StartupBackup\\', 'SYSTEM\\CurrentControlSet\\Control\\')
                else:
                    original_path = program_info['registry_path'].replace('StartupBackup\\', 'Microsoft\\Windows\\CurrentVersion\\')
                with winreg.CreateKey(program_info['registry_key'], original_path) as key:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, program_info['path'])
                with winreg.OpenKey(program_info['registry_key'], program_info['registry_path'], 0, winreg.KEY_SET_VALUE) as backup_key:
                    winreg.DeleteValue(backup_key, name)
            elif program_info.get('is_disabled_by_taskmanager') or program_info['status'] == 'Task Manager Devre Dışı':
                approved_path = program_info['registry_path'].replace('Microsoft\\Windows\\CurrentVersion\\', 'Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\')
                with winreg.OpenKey(program_info['registry_key'], approved_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
                    current_value, _ = winreg.QueryValueEx(key, name)
                    if len(current_value) >= 1:
                        new_value = bytearray(current_value)
                        new_value[0] = 0x02
                        winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, bytes(new_value))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_program(self, name):
        program_info = self.startup_programs.get(name)
        if not program_info: return {"success": False, "error": "Program bilgileri bulunamadı."}
        try:
            if program_info.get('is_folder_based'):
                file_path = program_info['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                if not program_info.get('is_backup') and not program_info.get('is_disabled_by_taskmanager'):
                    try:
                        with winreg.OpenKey(program_info['registry_key'], program_info['registry_path'], 0, winreg.KEY_SET_VALUE) as key:
                            winreg.DeleteValue(key, name)
                    except: pass
                if program_info.get('is_backup'):
                    try:
                        with winreg.OpenKey(program_info['registry_key'], program_info['registry_path'], 0, winreg.KEY_SET_VALUE) as key:
                            winreg.DeleteValue(key, name)
                    except: pass
                if program_info.get('is_disabled_by_taskmanager'):
                    approved_path = program_info['registry_path'].replace('Microsoft\\Windows\\CurrentVersion\\', 'Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\')
                    try:
                        with winreg.OpenKey(program_info['registry_key'], approved_path, 0, winreg.KEY_SET_VALUE) as key:
                            winreg.DeleteValue(key, name)
                    except: pass
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_location(self, path):
        try:
            file_path = self.extract_file_path(path)
            subprocess.run(['explorer', '/select,', file_path])
            logging.info(f"Opened location for: {file_path}")
        except Exception as e: 
            logging.error(f"Error opening location {path}: {str(e)}")

    def search_internet(self, name):
        query = urllib.parse.quote(name + " startup process")
        webbrowser.open(f"https://www.google.com/search?q={query}")
        logging.info(f"Searched internet for: {name}")

    def add_program(self):
        if not self.window: return {"success": False, "error": "No window"}
        result = self.window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=('Executable Files (*.exe)', 'All Files (*.*)'))
        if result and len(result) > 0:
            file_path = result[0]
            name = os.path.splitext(os.path.basename(file_path))[0]
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, file_path)
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": ""}

    def export_data(self):
        if not self.window: return {"success": False, "error": "No window"}
        result = self.window.create_file_dialog(webview.SAVE_DIALOG, directory=os.getcwd(), save_filename='startup_backup.json')
        if result:
            try:
                file_path = result if isinstance(result, str) else result[0]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.startup_programs, f, indent=2, ensure_ascii=False)
                return {"success": True, "path": file_path}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "İptal edildi"}

    def import_data(self):
        if not self.window: return {"success": False, "error": "No window"}
        result = self.window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=('JSON Files (*.json)', 'All Files (*.*)'))
        if result and len(result) > 0:
            try:
                file_path = result[0]
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                count = 0
                for name, info in import_data.items():
                    if not isinstance(info, dict) or 'path' not in info: continue
                    path = info['path'].strip('"').lower()
                    
                    try:
                        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, info['path'])
                        count += 1
                    except Exception:
                        pass
                return {"success": True, "count": count}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "İptal edildi"}

    # --- New Module Endpoints ---

    def get_registry_keys(self):
        keys_list = []
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM\\WOW6432Node\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\WOW6432Node\\RunOnce"),
        ]
        
        type_map = {
            winreg.REG_SZ: "REG_SZ",
            winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
            winreg.REG_BINARY: "REG_BINARY",
            winreg.REG_DWORD: "REG_DWORD",
            winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
        }

        for hkey, subkey_path, location_name in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, reg_type = winreg.EnumValue(key, i)
                            if name.strip():
                                type_str = type_map.get(reg_type, f"UNKNOWN ({reg_type})")
                                data_str = str(value) if not isinstance(value, bytes) else value.hex()
                                keys_list.append({
                                    "location": location_name,
                                    "name": name,
                                    "type": type_str,
                                    "data": data_str
                                })
                            i += 1
                        except WindowsError:
                            break
            except Exception:
                pass
        
        return {"success": True, "keys": keys_list}

    def get_logs(self):
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'startup_control.log')
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return "Log dosyası henüz oluşturulmadı."
        except Exception as e:
            return f"Loglar okunurken hata: {str(e)}"

    def clear_logs(self):
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'startup_control.log')
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("")
            logging.info("Logs cleared by user")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_services(self):
        services = []
        try:
            for svc in psutil.win_service_iter():
                try:
                    info = svc.as_dict()
                    services.append({
                        "name": info.get('name', ''),
                        "display_name": info.get('display_name', ''),
                        "status": info.get('status', ''),
                        "start_type": info.get('start_type', ''),
                        "description": info.get('description', '')
                    })
                except psutil.AccessDenied:
                    pass
                except Exception:
                    pass
            logging.info(f"Retrieved {len(services)} services")
            return {"success": True, "services": services}
        except Exception as e:
            logging.error(f"Error fetching services: {str(e)}")
            return {"success": False, "error": str(e)}

    def start_service(self, name):
        try:
            svc = psutil.win_service_get(name)
            svc.start()
            logging.info(f"Started service: {name}")
            return {"success": True}
        except Exception as e:
            logging.error(f"Error starting service {name}: {str(e)}")
            return {"success": False, "error": str(e)}

    def stop_service(self, name):
        try:
            svc = psutil.win_service_get(name)
            svc.stop()
            logging.info(f"Stopped service: {name}")
            return {"success": True}
        except Exception as e:
            logging.error(f"Error stopping service {name}: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_settings(self):
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"theme": "dark", "lang": "tr", "backup_dir": os.getcwd()}

    def save_settings(self, settings):
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            logging.info("Settings saved")
            return {"success": True}
        except Exception as e:
            logging.error(f"Error saving settings: {str(e)}")
            return {"success": False, "error": str(e)}

    def open_url(self, url):
        try:
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_internet(self):
        hosts = [("8.8.8.8", 53), ("1.1.1.1", 53), ("8.8.4.4", 53), ("1.0.0.1", 53), ("google.com", 80), ("api.github.com", 443), ("api.github.com", 80), ("github.com", 443), ("github.com", 80), ("github.global.ssl.fastly.net", 443), ("github.global.ssl.fastly.net", 80), ("githubusercontent.com", 443), ("githubusercontent.com", 80)]
        for host, port in hosts:
            try:
                socket.setdefaulttimeout(1)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                return True
            except Exception:
                pass
        return False

    def check_for_updates(self):
        try:
            if not self.check_internet():
                return {"success": False, "update_available": False, "error": "No internet connection."}
            
            url = "https://api.github.com/repos/BartuAbiHD/BAHD-Win-StartUp-Control/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                latest_tag = data.get("tag_name", "")
                
                # Simple version compare (e.g. "v1.1.0" vs "1.0.0")
                latest_version = latest_tag.replace("v", "")
                if latest_version and latest_version != self.VERSION:
                    # Basic string comparison might not work for 1.10.0 > 1.9.0 but usually works for simple bumps
                    # Let's consider any different version as an update if it's not the same
                    return {
                        "success": True, 
                        "update_available": True, 
                        "latest_version": latest_tag, 
                        "release_url": data.get("html_url", "https://github.com/BartuAbiHD/BAHD-Win-StartUp-Control/releases")
                    }
            return {"success": True, "update_available": False}
        except Exception as e:
            logging.error(f"Update check failed: {str(e)}")
            return {"success": False, "update_available": False, "error": str(e)}

if __name__ == '__main__':
    import sys
    
    api = StartupApi()
    
    # Handle PyInstaller paths
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # URL to the local web folder
    url = os.path.join(base_path, 'web', 'index.html')
    
    window = webview.create_window('BAHD Win StartUp Control', url, js_api=api, width=1200, height=800, background_color='#0b1120')
    api.set_window(window)
    
    # We pass debugging as False for production to prevent AccessibilityObject log spam
    webview.start(debug=False, icon=os.path.join(base_path, 'icon.ico'))
