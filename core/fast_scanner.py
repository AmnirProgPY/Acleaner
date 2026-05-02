"""
Python stub for fast_scanner C extension
This allows Pylance to understand the module structure without compiling
"""

import os
import glob

class FastScanner:
    """Pure Python implementation that mirrors the C extension API"""
    
    @staticmethod
    def scan(root_path, pattern="*", max_depth=-1, min_size=0):
        """
        Scan directory for files matching pattern
        
        Args:
            root_path: Root directory to scan
            pattern: File pattern to match (e.g., "*.tmp")
            max_depth: Maximum directory depth (-1 for unlimited)
            min_size: Minimum file size in bytes
            
        Returns:
            List of dictionaries with file information
        """
        results = []
        
        search_path = os.path.join(root_path, pattern)
        
        try:
            for filepath in glob.glob(search_path, recursive=True):
                if os.path.isfile(filepath):
                    try:
                        stat = os.stat(filepath)
                        if stat.st_size >= min_size:
                            results.append({
                                'path': filepath,
                                'size': stat.st_size,
                                'modified': stat.st_mtime
                            })
                    except (OSError, PermissionError):
                        continue
        except Exception as e:
            print(f"Scan error: {e}")
        
        return results
    
    @staticmethod
    def delete_files(file_list):
        """
        Delete files and return total freed space
        
        Args:
            file_list: List of dicts with 'path' key or list of strings
            
        Returns:
            Total bytes freed
        """
        total_freed = 0
        
        for item in file_list:
            try:
                if isinstance(item, dict):
                    filepath = item.get('path', '')
                else:
                    filepath = str(item)
                
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    total_freed += size
            except (OSError, PermissionError, FileNotFoundError):
                continue
        
        return total_freed
    
    @staticmethod
    def analyze_disk(path):
        """
        Analyze disk space usage
        
        Args:
            path: Path to analyze
            
        Returns:
            Dictionary with disk space information
        """
        import shutil
        
        try:
            stats = shutil.disk_usage(path)
            return {
                'total_space': stats.total,
                'free_space': stats.free,
                'used_space': stats.used
            }
        except Exception as e:
            print(f"Disk analysis error: {e}")
            return {
                'total_space': 0,
                'free_space': 0,
                'used_space': 0
            }