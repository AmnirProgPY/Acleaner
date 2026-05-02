"""
System Cleaner Module
Handles system junk file detection and cleaning
"""

import os
import shutil
import tempfile
import platform
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class SystemCleaner:
    """Main system cleaning functionality"""
    
    def __init__(self):
        self.system = platform.system()
        self.temp_locations = self._get_temp_locations()
        self.log_locations = self._get_log_locations()
        self.cache_locations = self._get_cache_locations()
    
    def _get_temp_locations(self) -> List[str]:
        """Get system-specific temporary file locations"""
        locations = []
        
        if self.system == 'Windows':
            locations.extend([
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                r'C:\Windows\Temp',
                r'C:\Windows\Prefetch',
                os.path.expandvars(r'%USERPROFILE%\AppData\Local\Temp'),
            ])
        else:  # Linux/Mac
            locations.extend([
                '/tmp',
                '/var/tmp',
                os.path.expanduser('~/.cache'),
            ])
        
        return [loc for loc in locations if loc and os.path.exists(loc)]
    
    def _get_log_locations(self) -> List[str]:
        """Get system log file locations"""
        locations = []
        
        if self.system == 'Windows':
            locations.extend([
                r'C:\Windows\Logs',
                r'C:\Windows\System32\LogFiles',
                os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Windows\Explorer'),
            ])
        else:
            locations.extend([
                '/var/log',
                os.path.expanduser('~/.local/share/xorg'),
            ])
        
        return [loc for loc in locations if loc and os.path.exists(loc)]
    
    def _get_cache_locations(self) -> List[str]:
        """Get system cache locations"""
        locations = []
        
        if self.system == 'Windows':
            locations.extend([
                os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Windows\INetCache'),
                os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Windows\WER'),
                r'C:\ProgramData\Microsoft\Windows\WER',
            ])
        else:
            locations.extend([
                os.path.expanduser('~/.cache/thumbnails'),
                os.path.expanduser('~/.cache/mesa_shader_cache'),
            ])
        
        return [loc for loc in locations if loc and os.path.exists(loc)]
    
    def scan_temp_files(self, days_old=1) -> Dict:
        """
        Scan for temporary files older than specified days
        
        Args:
            days_old: Files older than this many days will be included
            
        Returns:
            Dictionary with files list and total size
        """
        junk_files = []
        total_size = 0
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        # Known temporary file extensions
        temp_extensions = {
            '.tmp', '.temp', '.bak', '.old', '.log', '.dmp',
            '.cache', '.$$$', '.~*', '._*'
        }
        
        # Scan all temporary locations
        for location in self.temp_locations + self.log_locations + self.cache_locations:
            try:
                for root, dirs, files in os.walk(location):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Check file extension and age
                            file_stat = os.stat(file_path)
                            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            ext = os.path.splitext(file)[1].lower()
                            
                            if ext in temp_extensions or file_mtime < cutoff_time:
                                size = file_stat.st_size
                                junk_files.append({
                                    'path': file_path,
                                    'size': size,
                                    'modified': file_mtime.isoformat()
                                })
                                total_size += size
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue
        
        return {
            'files': junk_files,
            'size': total_size
        }
    
    def clean_files(self, file_list: List[Dict]) -> int:
        """
        Clean specified files
        
        Args:
            file_list: List of file dictionaries with 'path' key
            
        Returns:
            Total size of files removed
        """
        total_cleaned = 0
        
        for file_info in file_list:
            file_path = file_info['path']
            try:
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_cleaned += size
                elif os.path.isdir(file_path):
                    # Get directory size before removal
                    size = self._get_dir_size(file_path)
                    shutil.rmtree(file_path)
                    total_cleaned += size
            except (OSError, PermissionError, FileNotFoundError):
                continue
        
        return total_cleaned
    
    def scan_registry(self) -> Dict:
        """
        Scan Windows registry for issues (Windows only placeholder)
        """
        if self.system != 'Windows':
            return {'issues': [], 'count': 0}
        
        issues = []
        
        # In a real implementation, this would use winreg to scan
        # for invalid entries, missing file associations, etc.
        # This is a simplified placeholder
        
        registry_paths = [
            r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
            r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        ]
        
        # Placeholder for demonstration
        issues.append({
            'type': 'invalid_path',
            'key': r'HKEY_LOCAL_MACHINE\SOFTWARE\Example\MissingFile',
            'description': 'File reference points to missing file'
        })
        
        return {
            'issues': issues,
            'count': len(issues)
        }
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """Calculate total size of a directory"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += SystemCleaner._get_dir_size(entry.path)
        except (OSError, PermissionError):
            pass
        return total