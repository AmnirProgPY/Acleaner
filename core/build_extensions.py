"""
Build script for compiling C and C++ extensions
Updated for Python 3.12+ compatibility
"""

import sys
import os
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext  # Changed from distutils

class BuildExt(build_ext):
    """Custom build extension for handling C and C++ files"""
    
    def build_extensions(self):
        # Add compiler-specific flags
        compiler_type = self.compiler.compiler_type
        
        for ext in self.extensions:
            if ext.language == 'c++':
                if compiler_type == 'msvc':
                    ext.extra_compile_args.extend(['/std:c++17', '/O2'])
                else:
                    ext.extra_compile_args.extend(['-std=c++17', '-O3', '-march=native'])
            elif ext.language == 'c':
                if compiler_type == 'msvc':
                    ext.extra_compile_args.extend(['/O2'])
                else:
                    ext.extra_compile_args.extend(['-O3', '-march=native'])
        
        super().build_extensions()

# Define extensions conditionally
extensions = []

# Fast scanner extension (C)
fast_scanner_ext = Extension(
    'fast_scanner',  # Changed to match import in main.py
    sources=['src/core/fast_scanner.c'],
    language='c',
)

# File operations extension (C++)
file_ops_ext = Extension(
    'file_ops',
    sources=['src/core/file_ops.cpp'],
    language='c++',
)

# Only add extensions if their source files exist
if os.path.exists('src/core/fast_scanner.c'):
    extensions.append(fast_scanner_ext)

if os.path.exists('src/core/file_ops.cpp'):
    # Add OpenSSL libraries conditionally
    if sys.platform == 'win32':
        file_ops_ext.libraries = ['libssl', 'libcrypto']
    else:
        file_ops_ext.libraries = ['ssl', 'crypto']
    extensions.append(file_ops_ext)

if __name__ == "__main__":
    if not extensions:
        print("Warning: No extension source files found!")
        sys.exit(0)
    
    setup(
        name='ccleaner_clone',
        version='1.0.0',
        description='System cleaning utility with C/C++ optimizations',
        ext_modules=extensions,
        cmdclass={'build_ext': BuildExt},
        python_requires='>=3.8',
    )