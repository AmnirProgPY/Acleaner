"""
Analyzer package for disk and file analysis
"""

from .disk_analyzer import DiskAnalyzer, quick_disk_check
from .duplicate_finder import DuplicateFinder

__all__ = ['DiskAnalyzer', 'DuplicateFinder', 'quick_disk_check']