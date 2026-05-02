"""
Core module package
Handles both compiled extensions and Python stubs
"""

# Try to import compiled C extension first
try:
    from .fast_scanner import FastScanner
    print("✓ Using compiled C fast_scanner extension")
except ImportError:
    # Fall back to Python stub
    try:
        from .fast_scanner import FastScanner
        print("✓ Using Python fast_scanner stub")
    except ImportError:
        print("✗ No fast_scanner available")
        FastScanner = None

# Try to import compiled C++ extension functions
try:
    from .file_ops import secure_delete, find_duplicates, calculate_hash
    print("✓ Using compiled C++ file_ops extension")
except (ImportError, SyntaxError):
    # Fall back to Python stub
    try:
        from .file_ops import secure_delete, find_duplicates, calculate_hash
        print("✓ Using Python file_ops stub")
    except ImportError:
        print("✗ No file_ops available")
        # Define empty placeholders
        def secure_delete(filepath, passes=3):
            import os
            try:
                os.remove(filepath)
                return True
            except:
                return False
        
        def find_duplicates(directory):
            return {}
        
        def calculate_hash(filepath):
            return ""

__all__ = ['FastScanner', 'secure_delete', 'find_duplicates', 'calculate_hash']