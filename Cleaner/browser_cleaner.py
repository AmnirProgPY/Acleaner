"""
Browser Cache Cleaner Module
Cleans cache, cookies, and history from major browsers
"""

import os
import shutil
import sqlite3
import platform
from pathlib import Path
from typing import Dict, List

class BrowserCleaner:
    """Handles cleaning of browser data"""
    
    def __init__(self):
        self.system = platform.system()
        self.browsers = self._detect_browsers()
    
    def _detect_browsers(self) -> Dict[str, List[str]]:
        """Detect installed browsers and their cache locations"""
        browsers = {}
        
        if self.system == 'Windows':
            base_path = os.environ.get('LOCALAPPDATA', '')
            
            # Chrome
            chrome_path = os.path.join(base_path, r'Google\Chrome\User Data')
            if os.path.exists(chrome_path):
                browsers['Chrome'] = [os.path.join(chrome_path, d) for d in os.listdir(chrome_path) 
                                     if d.startswith('Profile') or d == 'Default']
            
            # Firefox
            firefox_path = os.path.join(os.environ.get('APPDATA', ''), r'Mozilla\Firefox\Profiles')
            if os.path.exists(firefox_path):
                browsers['Firefox'] = [os.path.join(firefox_path, d) for d in os.listdir(firefox_path)]
            
            # Edge
            edge_path = os.path.join(base_path, r'Microsoft\Edge\User Data')
            if os.path.exists(edge_path):
                browsers['Edge'] = [os.path.join(edge_path, d) for d in os.listdir(edge_path)
                                  if d.startswith('Profile') or d == 'Default']
        
        elif self.system == 'Linux':
            home = os.path.expanduser('~')
            
            if os.path.exists(os.path.join(home, '.config/google-chrome')):
                browsers['Chrome'] = [os.path.join(home, '.config/google-chrome')]
            
            if os.path.exists(os.path.join(home, '.mozilla/firefox')):
                browsers['Firefox'] = [os.path.join(home, '.mozilla/firefox')]
        
        elif self.system == 'Darwin':  # macOS
            home = os.path.expanduser('~')
            library = os.path.join(home, 'Library')
            
            chrome_path = os.path.join(library, 'Application Support/Google/Chrome')
            if os.path.exists(chrome_path):
                browsers['Chrome'] = [chrome_path]
            
            firefox_path = os.path.join(library, 'Application Support/Firefox/Profiles')
            if os.path.exists(firefox_path):
                browsers['Firefox'] = [os.path.join(firefox_path, d) for d in os.listdir(firefox_path)]
        
        return browsers
    
    def scan_all_browsers(self) -> Dict:
        """
        Scan all detected browsers for cache files
        
        Returns:
            Dictionary with files list and total size
        """
        cache_files = []
        total_size = 0
        
        cache_subdirs = ['Cache', 'Code Cache', 'GPUCache', 'Service Worker']
        
        for browser, profiles in self.browsers.items():
            for profile in profiles:
                # Scan cache directories
                for subdir in cache_subdirs:
                    cache_path = os.path.join(profile, subdir)
                    if os.path.exists(cache_path):
                        for root, dirs, files in os.walk(cache_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    size = os.path.getsize(file_path)
                                    cache_files.append({
                                        'path': file_path,
                                        'size': size,
                                        'browser': browser
                                    })
                                    total_size += size
                                except (OSError, PermissionError):
                                    continue
                
                # Scan cookies and history databases
                for db_file in ['Cookies', 'History', 'Web Data']:
                    db_path = os.path.join(profile, db_file)
                    if os.path.exists(db_path):
                        try:
                            size = os.path.getsize(db_path)
                            cache_files.append({
                                'path': db_path,
                                'size': size,
                                'browser': browser,
                                'type': 'database'
                            })
                            total_size += size
                        except (OSError, PermissionError):
                            continue
        
        return {
            'files': cache_files,
            'size': total_size
        }
    
    def clean_all(self) -> int:
        """
        Clean all browser caches
        
        Returns:
            Total size cleaned
        """
        total_cleaned = 0
        scan_result = self.scan_all_browsers()
        
        for file_info in scan_result['files']:
            try:
                file_path = file_info['path']
                
                if file_info.get('type') == 'database':
                    # Vacuum database instead of deleting
                    if os.path.exists(file_path):
                        try:
                            conn = sqlite3.connect(file_path)
                            conn.execute('VACUUM')
                            conn.close()
                            new_size = os.path.getsize(file_path)
                            total_cleaned += file_info['size'] - new_size
                        except:
                            # If vacuum fails, try to remove
                            os.remove(file_path)
                            total_cleaned += file_info['size']
                else:
                    # Remove cache files
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        total_cleaned += file_info['size']
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        total_cleaned += file_info['size']
                        
            except (OSError, PermissionError):
                continue
        
        return total_cleaned