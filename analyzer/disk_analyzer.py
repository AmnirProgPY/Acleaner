"""
Disk Analyzer Module
Analyzes disk space usage and provides visualization data
"""

import os
import platform
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

class DiskAnalyzer:
    """Analyzes disk space usage and identifies large files/folders"""
    
    def __init__(self):
        self.system = platform.system()
    
    def get_disk_info(self) -> List[Dict]:
        """
        Get information about all disk drives
        
        Returns:
            List of dictionaries with drive information
        """
        drives = []
        
        if self.system == 'Windows':
            import string
            from ctypes import windll
            
            # Get all drive letters
            drives_list = []
            bitmask = windll.kernel32.GetLogicalDrives()
            
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive_path = f"{letter}:\\"
                    if os.path.exists(drive_path):
                        drives_list.append(drive_path)
                bitmask >>= 1
            
            for drive in drives_list:
                try:
                    total, used, free = self._get_disk_usage(drive)
                    drive_type = self._get_drive_type_windows(drive)
                    
                    drives.append({
                        'path': drive,
                        'label': self._get_drive_label_windows(drive),
                        'type': drive_type,
                        'total': total,
                        'used': used,
                        'free': free,
                        'percent_used': (used / total * 100) if total > 0 else 0
                    })
                except:
                    continue
        
        elif self.system == 'Linux':
            # Check common mount points
            mount_points = ['/', '/home', '/tmp', '/var']
            
            for mount in mount_points:
                if os.path.exists(mount):
                    try:
                        total, used, free = self._get_disk_usage(mount)
                        drives.append({
                            'path': mount,
                            'label': mount,
                            'type': 'ext4',
                            'total': total,
                            'used': used,
                            'free': free,
                            'percent_used': (used / total * 100) if total > 0 else 0
                        })
                    except:
                        continue
        
        elif self.system == 'Darwin':  # macOS
            mount_point = '/'
            try:
                total, used, free = self._get_disk_usage(mount_point)
                drives.append({
                    'path': mount_point,
                    'label': 'Macintosh HD',
                    'type': 'APFS',
                    'total': total,
                    'used': used,
                    'free': free,
                    'percent_used': (used / total * 100) if total > 0 else 0
                })
            except:
                pass
        
        return drives
    
    def analyze_directory(self, path: str, top_n: int = 20) -> Dict:
        """
        Analyze a directory and find largest files/folders
        
        Args:
            path: Directory path to analyze
            top_n: Number of top items to return
            
        Returns:
            Dictionary with analysis results
        """
        if not os.path.exists(path):
            return {'error': f'Path does not exist: {path}'}
        
        results = {
            'path': path,
            'total_size': 0,
            'file_count': 0,
            'directory_count': 0,
            'largest_files': [],
            'largest_directories': [],
            'extension_stats': defaultdict(lambda: {'count': 0, 'size': 0}),
            'size_distribution': {
                'tiny': {'count': 0, 'size': 0},    # < 1MB
                'small': {'count': 0, 'size': 0},    # 1MB - 10MB
                'medium': {'count': 0, 'size': 0},   # 10MB - 100MB
                'large': {'count': 0, 'size': 0},    # 100MB - 1GB
                'huge': {'count': 0, 'size': 0}      # > 1GB
            }
        }
        
        try:
            # Collect all files and directories with sizes
            all_items = []
            dir_sizes = defaultdict(int)
            
            for root, dirs, files in os.walk(path):
                # Skip system directories
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
                
                # Analyze files
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(filepath)
                        results['file_count'] += 1
                        results['total_size'] += size
                        
                        # Track extension statistics
                        ext = os.path.splitext(filename)[1].lower() or '(no extension)'
                        results['extension_stats'][ext]['count'] += 1
                        results['extension_stats'][ext]['size'] += size
                        
                        # Size distribution
                        self._categorize_by_size(size, results['size_distribution'])
                        
                        # Add to items list
                        all_items.append({
                            'path': filepath,
                            'name': filename,
                            'size': size,
                            'type': 'file'
                        })
                        
                        # Add to parent directory size
                        parent = os.path.dirname(filepath)
                        dir_sizes[parent] += size
                        
                    except (OSError, PermissionError):
                        continue
                
                # Count directories
                for dirname in dirs:
                    results['directory_count'] += 1
            
            # Add directory sizes to items
            for dirpath, size in dir_sizes.items():
                all_items.append({
                    'path': dirpath,
                    'name': os.path.basename(dirpath),
                    'size': size,
                    'type': 'directory'
                })
            
            # Sort by size and get top items
            all_items.sort(key=lambda x: x['size'], reverse=True)
            
            # Separate into files and directories
            results['largest_files'] = [item for item in all_items if item['type'] == 'file'][:top_n]
            results['largest_directories'] = [item for item in all_items if item['type'] == 'directory'][:top_n]
            
            # Convert defaultdict to regular dict for extension_stats
            results['extension_stats'] = dict(results['extension_stats'])
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _get_disk_usage(self, path: str) -> Tuple[int, int, int]:
        """
        Get disk usage statistics
        
        Returns:
            Tuple of (total, used, free) in bytes
        """
        try:
            import shutil
            stats = shutil.disk_usage(path)
            return stats.total, stats.used, stats.free
        except:
            # Fallback for older Python versions
            if self.system == 'Windows':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(path), 
                    None, 
                    ctypes.pointer(total_bytes), 
                    ctypes.pointer(free_bytes)
                )
                total = total_bytes.value
                free = free_bytes.value
                used = total - free
                return total, used, free
            else:
                import os
                stat = os.statvfs(path)
                total = stat.f_frsize * stat.f_blocks
                free = stat.f_frsize * stat.f_bfree
                used = total - free
                return total, used, free
    
    def _get_drive_type_windows(self, drive: str) -> str:
        """Get Windows drive type"""
        try:
            import ctypes
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            
            types = {
                0: 'Unknown',
                1: 'No Root Directory',
                2: 'Removable',
                3: 'Fixed',
                4: 'Network',
                5: 'CD-ROM',
                6: 'RAM Disk'
            }
            
            return types.get(drive_type, 'Unknown')
        except:
            return 'Unknown'
    
    def _get_drive_label_windows(self, drive: str) -> str:
        """Get Windows drive label"""
        try:
            import ctypes
            volume_name = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetVolumeInformationW(
                drive, volume_name, 1024, None, None, None, None, 0
            )
            return volume_name.value or drive
        except:
            return drive
    
    def _should_skip_dir(self, dirname: str) -> bool:
        """Check if directory should be skipped"""
        skip_dirs = {
            '$RECYCLE.BIN', 'System Volume Information', 
            'Recovery', 'Windows', 'Program Files', 'Program Files (x86)',
            '.git', 'node_modules', '__pycache__'
        }
        return dirname in skip_dirs or dirname.startswith('.')
    
    def _categorize_by_size(self, size: int, distribution: Dict):
        """Categorize file by size"""
        if size < 1024 * 1024:  # < 1MB
            distribution['tiny']['count'] += 1
            distribution['tiny']['size'] += size
        elif size < 10 * 1024 * 1024:  # < 10MB
            distribution['small']['count'] += 1
            distribution['small']['size'] += size
        elif size < 100 * 1024 * 1024:  # < 100MB
            distribution['medium']['count'] += 1
            distribution['medium']['size'] += size
        elif size < 1024 * 1024 * 1024:  # < 1GB
            distribution['large']['count'] += 1
            distribution['large']['size'] += size
        else:
            distribution['huge']['count'] += 1
            distribution['huge']['size'] += size
    
    def generate_report(self, path: str = None) -> str:
        """
        Generate a text-based disk usage report
        
        Args:
            path: Path to analyze (defaults to user home or C:\)
            
        Returns:
            Formatted report string
        """
        if path is None:
            path = os.path.expanduser('~')
        
        drives = self.get_disk_info()
        analysis = self.analyze_directory(path)
        
        report = []
        report.append("=" * 60)
        report.append("DISK SPACE ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Drive information
        report.append("\n📊 DRIVE INFORMATION:")
        report.append("-" * 40)
        for drive in drives:
            report.append(f"Drive: {drive['path']} ({drive.get('label', 'Unknown')})")
            report.append(f"  Type: {drive['type']}")
            report.append(f"  Total: {self._format_size(drive['total'])}")
            report.append(f"  Used:  {self._format_size(drive['used'])} ({drive['percent_used']:.1f}%)")
            report.append(f"  Free:  {self._format_size(drive['free'])}")
        
        # Directory analysis
        if 'error' not in analysis:
            report.append(f"\n📁 ANALYSIS OF: {path}")
            report.append("-" * 40)
            report.append(f"Total Size: {self._format_size(analysis['total_size'])}")
            report.append(f"Files: {analysis['file_count']}")
            report.append(f"Directories: {analysis['directory_count']}")
            
            # Top largest files
            report.append(f"\n🔝 TOP 10 LARGEST FILES:")
            for item in analysis['largest_files'][:10]:
                report.append(f"  {self._format_size(item['size']):>10} - {item['name']}")
            
            # Top largest directories
            report.append(f"\n📂 TOP 10 LARGEST DIRECTORIES:")
            for item in analysis['largest_directories'][:10]:
                report.append(f"  {self._format_size(item['size']):>10} - {item['name']}")
            
            # Size distribution
            report.append(f"\n📊 SIZE DISTRIBUTION:")
            dist = analysis['size_distribution']
            for category, stats in dist.items():
                if stats['count'] > 0:
                    report.append(
                        f"  {category.capitalize():<7}: {stats['count']:>6} files "
                        f"({self._format_size(stats['size'])})"
                    )
            
            # File type statistics
            report.append(f"\n📄 TOP FILE TYPES:")
            extension_stats = sorted(
                analysis['extension_stats'].items(),
                key=lambda x: x[1]['size'],
                reverse=True
            )[:10]
            for ext, stats in extension_stats:
                report.append(
                    f"  {ext:<15}: {stats['count']:>6} files "
                    f"({self._format_size(stats['size'])})"
                )
        
        report.append("\n" + "=" * 60)
        return '\n'.join(report)
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


# Utility function for quick disk check
def quick_disk_check(path: str = None) -> Dict:
    """
    Quick disk space check without full analysis
    
    Args:
        path: Path to check (default: current directory)
        
    Returns:
        Dictionary with disk information
    """
    analyzer = DiskAnalyzer()
    
    if path is None:
        path = os.getcwd()
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        
        return {
            'path': path,
            'total_space': total,
            'used_space': used,
            'free_space': free,
            'percent_used': (used / total * 100) if total > 0 else 0,
            'percent_free': (free / total * 100) if total > 0 else 0
        }
    except Exception as e:
        return {'error': str(e)}