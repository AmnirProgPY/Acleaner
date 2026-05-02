"""
Duplicate File Finder Module
Uses hashing to identify duplicate files
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

class DuplicateFinder:
    """Finds duplicate files using size comparison and SHA-256 hashing"""
    
    def __init__(self, min_file_size=1024):
        self.min_file_size = min_file_size  # Skip files smaller than 1KB
    
    def find_duplicates(self, search_paths=None) -> Dict:
        """
        Find duplicate files in specified paths
        
        Args:
            search_paths: List of directories to search
            
        Returns:
            Dictionary with duplicate groups and wasted space info
        """
        if search_paths is None:
            search_paths = [
                os.path.expanduser('~'),
                '/home' if os.path.exists('/home') else None,
                'C:\\Users' if os.path.exists('C:\\Users') else None
            ]
            search_paths = [p for p in search_paths if p]
        
        # Stage 1: Group by file size
        size_map = defaultdict(list)
        
        for search_path in search_paths:
            for root, dirs, files in os.walk(search_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size >= self.min_file_size:
                            size_map[file_size].append(file_path)
                    except (OSError, PermissionError):
                        continue
        
        # Stage 2: Hash files with same size
        duplicates = {}
        wasted_space = 0
        
        for size, files in size_map.items():
            if len(files) < 2:
                continue
            
            hash_map = defaultdict(list)
            
            for file_path in files:
                try:
                    file_hash = self._get_file_hash(file_path)
                    if file_hash:
                        hash_map[file_hash].append(file_path)
                except (OSError, PermissionError):
                    continue
            
            # Find groups with duplicates
            for file_hash, dup_files in hash_map.items():
                if len(dup_files) > 1:
                    duplicates[file_hash] = dup_files
                    
                    # Calculate wasted space (all duplicates except one)
                    wasted_space += sum(size for _ in dup_files[1:])
        
        return {
            'groups': duplicates,
            'wasted_space': wasted_space
        }
    
    def _get_file_hash(self, file_path: str, chunk_size=65536) -> str:
        """
        Calculate SHA-256 hash of a file
        
        Args:
            file_path: Path to file
            chunk_size: Read chunk size for memory efficiency
            
        Returns:
            Hex digest string
        """
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (IOError, PermissionError):
            return ""