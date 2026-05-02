"""
Python stub for file_ops C++ extension
This allows Pylance to understand the module structure without compiling
"""

import os
import hashlib
from collections import defaultdict

def secure_delete(filepath, passes=3):
    """
    Securely delete a file by overwriting before removal
    
    Args:
        filepath: Path to file to delete
        passes: Number of overwrite passes
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(filepath):
            return False
        
        file_size = os.path.getsize(filepath)
        
        # Overwrite with random data multiple times
        with open(filepath, 'wb') as f:
            for _ in range(passes):
                f.seek(0)
                # Write random data in chunks
                remaining = file_size
                while remaining > 0:
                    chunk_size = min(remaining, 4096)
                    f.write(os.urandom(chunk_size))
                    remaining -= chunk_size
                f.flush()
                os.fsync(f.fileno())
        
        # Rename file before deletion (extra security)
        temp_name = filepath + '.deleted'
        os.rename(filepath, temp_name)
        os.remove(temp_name)
        
        return True
        
    except Exception as e:
        print(f"Secure delete error: {e}")
        # Fallback to simple delete
        try:
            os.remove(filepath)
            return True
        except:
            return False

def find_duplicates(directory):
    """
    Find duplicate files in directory
    
    Args:
        directory: Directory to search
        
    Returns:
        Dictionary mapping hash to list of duplicate files
    """
    if not os.path.exists(directory):
        return {}
    
    # Group files by size first
    size_map = defaultdict(list)
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                file_size = os.path.getsize(filepath)
                if file_size > 0:  # Skip empty files
                    size_map[file_size].append(filepath)
            except (OSError, PermissionError):
                continue
    
    # Hash files with same size
    duplicates = {}
    
    for size, file_list in size_map.items():
        if len(file_list) < 2:
            continue
        
        hash_map = defaultdict(list)
        
        for filepath in file_list:
            try:
                file_hash = calculate_hash(filepath)
                if file_hash:
                    hash_map[file_hash].append(filepath)
            except (OSError, PermissionError):
                continue
        
        # Find duplicate groups
        for file_hash, files in hash_map.items():
            if len(files) > 1:
                duplicates[file_hash] = files
    
    return duplicates

def calculate_hash(filepath):
    """
    Calculate SHA-256 hash of a file
    
    Args:
        filepath: Path to file
        
    Returns:
        Hex string of hash, or empty string on error
    """
    try:
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
        
    except (OSError, PermissionError, IOError) as e:
        print(f"Hash calculation error for {filepath}: {e}")
        return ""