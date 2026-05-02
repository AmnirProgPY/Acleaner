#!/usr/bin/env python3
"""
CCleaner Clone - System Cleaning Utility
Modern GUI using CustomTkinter
"""

import sys
import os
import ctypes
import platform
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Setup import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# CustomTkinter imports
import customtkinter as ctk
from tkinter import messagebox, filedialog, StringVar, IntVar, BooleanVar
from PIL import Image

# Configure CustomTkinter appearance
ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

# ============================================
# Import core modules with fallbacks
# ============================================

try:
    from core.fast_scanner import FastScanner
    print("✓ Native C fast scanner loaded")
except ImportError:
    print("⚠ Using Python fallback for fast scanner")
    
    class FastScanner:
        def scan(self, *args, **kwargs):
            return []
        def delete_files(self, *args, **kwargs):
            return 0
        def analyze_disk(self, *args, **kwargs):
            return {'total_space': 0, 'free_space': 0, 'used_space': 0}

try:
    from core.file_ops import secure_delete, find_duplicates, calculate_hash
    print("✓ Native C++ file operations loaded")
except ImportError:
    print("⚠ Using Python fallback for file operations")
    
    def secure_delete(filepath, passes=3):
        try:
            os.remove(filepath)
            return True
        except:
            return False
    
    def find_duplicates(directory):
        return {}
    
    def calculate_hash(filepath):
        return ""

try:
    from Cleaner.system_cleaner import SystemCleaner
except ImportError as e:
    print(f"✗ SystemCleaner import failed: {e}")
    sys.exit(1)

try:
    from Cleaner.browser_cleaner import BrowserCleaner
except ImportError as e:
    print(f"✗ BrowserCleaner import failed: {e}")
    sys.exit(1)

try:
    from analyzer.disk_analyzer import DiskAnalyzer
except ImportError as e:
    print(f"✗ DiskAnalyzer import failed: {e}")
    sys.exit(1)

try:
    from analyzer.duplicate_finder import DuplicateFinder
except ImportError as e:
    print(f"✗ DuplicateFinder import failed: {e}")
    sys.exit(1)


# ============================================
# Utility Functions
# ============================================

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def is_admin() -> bool:
    """Check if running with administrator privileges"""
    try:
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False


# ============================================
# Main Application GUI Class
# ============================================

class CCleanerApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Acleaner")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Set icon (optional)
        try:
            self.iconbitmap("icon.ico")
        except:
            pass
        
        # Initialize modules
        self.system_cleaner = SystemCleaner()
        self.browser_cleaner = BrowserCleaner()
        self.disk_analyzer = DiskAnalyzer()
        self.duplicate_finder = DuplicateFinder()
        self.fast_scanner = FastScanner()
        
        # Variables
        self.scanning = False
        self.cleaning = False
        self.current_frame = None
        self.scan_results = {}
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create UI components
        self._create_sidebar()
        self._create_main_content()
        self._create_status_bar()
        
        # Show dashboard by default
        self._show_dashboard()
    
    # ============================================
    # UI Creation Methods
    # ============================================
    
    def _create_sidebar(self):
        """Create the left sidebar navigation"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        # App logo/title
        logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="🧹 Acleaner",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Separator
        ctk.CTkLabel(self.sidebar, text="").grid(row=1, column=0, pady=5)
        
        # Navigation buttons
        nav_buttons = [
            ("📊 Dashboard", self._show_dashboard),
            ("🧹 System Cleaner", self._show_system_cleaner),
            ("🌐 Browser Cleaner", self._show_browser_cleaner),
            ("💾 Disk Analyzer", self._show_disk_analyzer),
            ("📁 Duplicate Finder", self._show_duplicate_finder),
            ("🔒 Secure Delete", self._show_secure_delete),
            ("⚙️ Settings", self._show_settings),
        ]
        
        self.nav_buttons = {}
        for i, (text, command) in enumerate(nav_buttons):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
            )
            btn.grid(row=i+2, column=0, padx=10, pady=3, sticky="ew")
            self.nav_buttons[text] = btn
        
        # App info at bottom
        info_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v1.0.0\n{platform.system()}",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        info_label.grid(row=9, column=0, padx=20, pady=10)
    
    def _create_main_content(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
    
    def _create_status_bar(self):
        """Create bottom status bar"""
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.grid(row=1, column=1, sticky="ew")
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Admin status
        admin_text = "🔒 Admin" if is_admin() else "⚠️ Limited"
        admin_color = "green" if is_admin() else "orange"
        admin_label = ctk.CTkLabel(
            self.status_frame,
            text=admin_text,
            font=ctk.CTkFont(size=11),
            text_color=admin_color
        )
        admin_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=200)
        self.progress_bar.set(0)
    
    def _clear_main_frame(self):
        """Clear all widgets from main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def _update_status(self, message: str, show_progress=False):
        """Update status bar message"""
        self.status_label.configure(text=message)
        if show_progress:
            self.progress_bar.grid(row=0, column=1, padx=10, pady=5)
            self.progress_bar.set(0)
        else:
            self.progress_bar.grid_forget()
    
    # ============================================
    # Dashboard View
    # ============================================
    
    def _show_dashboard(self):
        """Display the dashboard view"""
        self._clear_main_frame()
        
        # Title
        title = ctk.CTkLabel(
            self.main_frame,
            text="System Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Overview of your system health and cleaning options",
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        subtitle.pack(pady=(0, 30))
        
        # Stats cards in a scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Quick actions grid
        actions_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=10)
        
        actions = [
            ("🧹 Quick Clean", "Scan and clean common junk files", self._show_system_cleaner),
            ("🌐 Browser Clean", "Clear browser cache and cookies", self._show_browser_cleaner),
            ("💾 Disk Analysis", "Analyze disk usage and find large files", self._show_disk_analyzer),
            ("📁 Find Duplicates", "Find and remove duplicate files", self._show_duplicate_finder),
        ]
        
        for i, (title_text, desc, command) in enumerate(actions):
            col = i % 2
            row = i // 2
            
            card = ctk.CTkFrame(actions_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            card_title = ctk.CTkLabel(
                card,
                text=title_text,
                font=ctk.CTkFont(size=18, weight="bold")
            )
            card_title.pack(pady=(20, 5), padx=20)
            
            card_desc = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color="gray60"
            )
            card_desc.pack(pady=(0, 15), padx=20)
            
            card_btn = ctk.CTkButton(
                card,
                text="Open",
                command=command,
                width=100
            )
            card_btn.pack(pady=(0, 20))
        
        # Configure grid weights for action cards
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        
        # System stats
        stats_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        stats_frame.pack(fill="x", pady=10)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="System Statistics",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stats_title.pack(pady=15, padx=20, anchor="w")
        
        # Get disk info
        try:
            import shutil
            disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
            disk_stats = shutil.disk_usage(disk_path)
            
            stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stats_grid.pack(fill="x", padx=20, pady=10)
            
            # Total space
            ctk.CTkLabel(stats_grid, text="Total Space:", font=ctk.CTkFont(size=12)).grid(
                row=0, column=0, sticky="w", pady=5)
            ctk.CTkLabel(stats_grid, text=format_size(disk_stats.total), 
                        font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=0, column=1, sticky="w", pady=5)
            
            # Used space
            ctk.CTkLabel(stats_grid, text="Used Space:", font=ctk.CTkFont(size=12)).grid(
                row=1, column=0, sticky="w", pady=5)
            ctk.CTkLabel(stats_grid, text=format_size(disk_stats.used), 
                        font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=1, column=1, sticky="w", pady=5)
            
            # Free space
            ctk.CTkLabel(stats_grid, text="Free Space:", font=ctk.CTkFont(size=12)).grid(
                row=2, column=0, sticky="w", pady=5)
            ctk.CTkLabel(stats_grid, text=format_size(disk_stats.free), 
                        font=ctk.CTkFont(size=12, weight="bold"), text_color="green").grid(
                row=2, column=1, sticky="w", pady=5)
            
            # Usage bar
            usage_percent = (disk_stats.used / disk_stats.total) * 100
            ctk.CTkLabel(stats_grid, text="Usage:", font=ctk.CTkFont(size=12)).grid(
                row=3, column=0, sticky="w", pady=5)
            
            usage_bar = ctk.CTkProgressBar(stats_grid, width=200)
            usage_bar.set(usage_percent / 100)
            usage_bar.grid(row=3, column=1, sticky="w", pady=5)
            
            ctk.CTkLabel(stats_grid, text=f"{usage_percent:.1f}%", 
                        font=ctk.CTkFont(size=12)).grid(
                row=3, column=2, sticky="w", pady=5, padx=10)
            
        except Exception as e:
            ctk.CTkLabel(stats_frame, text=f"Unable to load stats: {e}",
                        text_color="red").pack(pady=10, padx=20)
    
    # ============================================
    # System Cleaner View
    # ============================================
    
    def _show_system_cleaner(self):
        """Display the system cleaner view"""
        self._clear_main_frame()
        
        # Title
        title = ctk.CTkLabel(
            self.main_frame,
            text="System Cleaner",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Clean temporary files and free up disk space",
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        subtitle.pack(pady=(0, 20))
        
        # Cleaning options
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Cleanup Categories",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15, padx=20, anchor="w")
        
        # Checkboxes for cleaning options
        self.clean_options = {}
        categories = [
            ("Temporary Files", True),
            ("System Logs", True),
            ("Recycle Bin", True),
            ("Memory Dumps", False),
            ("Error Reports", False),
            ("Prefetch Files", True),
            ("Thumbnail Cache", True),
        ]
        
        for category, default in categories:
            var = BooleanVar(value=default)
            self.clean_options[category] = var
            
            checkbox = ctk.CTkCheckBox(
                options_frame,
                text=category,
                variable=var,
                font=ctk.CTkFont(size=13)
            )
            checkbox.pack(pady=5, padx=30, anchor="w")
        
        # Results display
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.results_text = ctk.CTkTextbox(self.results_frame, height=150)
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.results_text.insert("1.0", "Scan results will appear here...")
        self.results_text.configure(state="disabled")
        
        # Action buttons
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        self.analyze_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Analyze",
            command=self._analyze_system,
            width=150,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.analyze_btn.pack(side="left", padx=10)
        
        self.clean_btn = ctk.CTkButton(
            button_frame,
            text="🧹 Clean Now",
            command=self._clean_system,
            width=150,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.clean_btn.pack(side="left", padx=10)
    
    def _analyze_system(self):
        """Analyze system for junk files"""
        if self.scanning:
            return
        
        self.scanning = True
        self.analyze_btn.configure(state="disabled", text="Scanning...")
        self._update_status("Scanning system...", show_progress=True)
        
        # Clear previous results
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "Scanning...\n")
        self.results_text.configure(state="disabled")
        
        # Run scan in background
        def scan_thread():
            try:
                # Simulate progress
                for i in range(101):
                    time.sleep(0.02)
                    self.progress_bar.set(i / 100)
                
                # Perform actual scan
                results = self.system_cleaner.scan_temp_files()
                
                self.after(0, lambda: self._display_scan_results(results))
            except Exception as e:
                self.after(0, lambda: self._update_status(f"Error: {e}"))
            finally:
                self.scanning = False
                self.after(0, lambda: self.analyze_btn.configure(state="normal", text="🔍 Analyze"))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _display_scan_results(self, results: Dict):
        """Display scan results in the text widget"""
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        
        if not results or not results.get('files'):
            self.results_text.insert("1.0", "No junk files found.\n")
        else:
            total_size = results.get('size', 0)
            files = results.get('files', [])
            
            self.results_text.insert("end", f"Found {len(files)} junk files\n")
            self.results_text.insert("end", f"Space that can be freed: {format_size(total_size)}\n")
            self.results_text.insert("end", "\n" + "="*50 + "\n")
            
            # Show first 50 files
            for file_info in files[:50]:
                file_path = file_info.get('path', '')
                file_size = format_size(file_info.get('size', 0))
                self.results_text.insert("end", f"{file_size:>10}  {file_path}\n")
            
            if len(files) > 50:
                self.results_text.insert("end", f"\n... and {len(files) - 50} more files")
            
            self.scan_results = results
        
        self.results_text.configure(state="disabled")
        self._update_status(f"Found {len(files)} files ({format_size(total_size)})")
    
    def _clean_system(self):
        """Clean found junk files"""
        if not self.scan_results or not self.scan_results.get('files'):
            messagebox.showinfo("No Results", "Please analyze first before cleaning.")
            return
        
        if self.cleaning:
            return
        
        # Confirm cleaning
        proceed = messagebox.askyesno(
            "Confirm Clean",
            f"Delete {len(self.scan_results['files'])} files?\n"
            f"Space to free: {format_size(self.scan_results['size'])}"
        )
        
        if not proceed:
            return
        
        self.cleaning = True
        self.clean_btn.configure(state="disabled", text="Cleaning...")
        self._update_status("Cleaning...", show_progress=True)
        
        def clean_thread():
            try:
                for i in range(101):
                    time.sleep(0.02)
                    self.progress_bar.set(i / 100)
                
                cleaned = self.system_cleaner.clean_files(self.scan_results['files'])
                self.after(0, lambda: self._after_clean(cleaned))
            except Exception as e:
                self.after(0, lambda: self._update_status(f"Error: {e}"))
            finally:
                self.cleaning = False
                self.after(0, lambda: self.clean_btn.configure(state="normal", text="🧹 Clean Now"))
        
        threading.Thread(target=clean_thread, daemon=True).start()
    
    def _after_clean(self, cleaned_bytes: int):
        """Actions after cleaning completes"""
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"✅ Cleaning complete!\nFreed: {format_size(cleaned_bytes)}")
        self.results_text.configure(state="disabled")
        
        self._update_status(f"Cleaned {format_size(cleaned_bytes)}")
        messagebox.showinfo("Success", f"Successfully freed {format_size(cleaned_bytes)}")
        self.scan_results = {}
    
    # ============================================
    # Browser Cleaner View
    # ============================================
    
    def _show_browser_cleaner(self):
        """Display the browser cleaner view"""
        self._clear_main_frame()
        
        title = ctk.CTkLabel(
            self.main_frame,
            text="Browser Cleaner",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Clear browser cache, cookies, and history",
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        subtitle.pack(pady=(0, 20))
        
        # Browser options
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Browser Data to Clean",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15, padx=20, anchor="w")
        
        self.browser_options = {}
        browser_categories = [
            ("Cache Files", True),
            ("Cookies", False),
            ("Browsing History", True),
            ("Download History", True),
            ("Saved Passwords", False),
            ("Form Data", False),
        ]
        
        for category, default in browser_categories:
            var = BooleanVar(value=default)
            self.browser_options[category] = var
            
            checkbox = ctk.CTkCheckBox(
                options_frame,
                text=category,
                variable=var,
                font=ctk.CTkFont(size=13)
            )
            checkbox.pack(pady=5, padx=30, anchor="w")
        
        # Detected browsers
        browsers = self.browser_cleaner.browsers
        browsers_frame = ctk.CTkFrame(self.main_frame)
        browsers_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            browsers_frame,
            text="Detected Browsers",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15, padx=20, anchor="w")
        
        if browsers:
            for browser, profiles in browsers.items():
                text = f"  {browser} ({len(profiles)} profile(s))"
                ctk.CTkLabel(
                    browsers_frame,
                    text=text,
                    font=ctk.CTkFont(size=13)
                ).pack(pady=3, padx=30, anchor="w")
        else:
            ctk.CTkLabel(
                browsers_frame,
                text="  No browsers detected",
                text_color="gray60"
            ).pack(pady=10, padx=30, anchor="w")
        
        # Action buttons
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        analyze_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Scan Browsers",
            command=self._scan_browsers,
            width=150,
            height=40
        )
        analyze_btn.pack(side="left", padx=10)
        
        clean_btn = ctk.CTkButton(
            button_frame,
            text="🧹 Clean All",
            command=self._clean_browsers,
            width=150,
            height=40,
            fg_color="green",
            hover_color="darkgreen"
        )
        clean_btn.pack(side="left", padx=10)
    
    def _scan_browsers(self):
        """Scan browser caches"""
        self._update_status("Scanning browsers...", show_progress=True)
        
        def scan():
            results = self.browser_cleaner.scan_all_browsers()
            total_size = results.get('size', 0)
            total_files = len(results.get('files', []))
            
            messagebox.showinfo(
                "Scan Results",
                f"Found {total_files} files\nSpace: {format_size(total_size)}"
            )
            
            self._update_status(f"Found {total_files} browser files")
        
        threading.Thread(target=scan, daemon=True).start()
    
    def _clean_browsers(self):
        """Clean browser data"""
        proceed = messagebox.askyesno("Confirm", "Clean all browser data?")
        if not proceed:
            return
        
        self._update_status("Cleaning browsers...", show_progress=True)
        
        def clean():
            cleaned = self.browser_cleaner.clean_all()
            self.after(0, lambda: self._update_status(f"Cleaned {format_size(cleaned)}"))
            messagebox.showinfo("Success", f"Cleaned {format_size(cleaned)}")
        
        threading.Thread(target=clean, daemon=True).start()
    
    # ============================================
    # Disk Analyzer View
    # ============================================
    
    def _show_disk_analyzer(self):
        """Display the disk analyzer view"""
        self._clear_main_frame()
        
        title = ctk.CTkLabel(
            self.main_frame,
            text="Disk Analyzer",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Analyze disk space and find large files",
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        subtitle.pack(pady=(0, 20))
        
        # Directory selection
        select_frame = ctk.CTkFrame(self.main_frame)
        select_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            select_frame,
            text="Select Directory to Analyze",
            font=ctk.CTkFont(size=14)
        ).pack(pady=10, padx=20, anchor="w")
        
        path_var = StringVar(value=os.path.expanduser('~'))
        
        path_entry = ctk.CTkEntry(
            select_frame,
            textvariable=path_var,
            height=35
        )
        path_entry.pack(fill="x", padx=20, pady=(0, 5))
        
        def browse():
            directory = filedialog.askdirectory()
            if directory:
                path_var.set(directory)
        
        browse_btn = ctk.CTkButton(
            select_frame,
            text="Browse",
            command=browse,
            width=100
        )
        browse_btn.pack(pady=(0, 15), padx=20, anchor="w")
        
        # Results area
        self.disk_results = ctk.CTkTextbox(self.main_frame, height=200)
        self.disk_results.pack(fill="both", expand=True, padx=30, pady=10)
        self.disk_results.insert("1.0", "Analysis results will appear here...")
        
        # Analyze button
        def analyze():
            path = path_var.get()
            if not os.path.exists(path):
                messagebox.showerror("Error", "Path does not exist!")
                return
            
            self._update_status(f"Analyzing {path}...", show_progress=True)
            
            def analyze_thread():
                try:
                    results = self.disk_analyzer.analyze_directory(path)
                    self.after(0, lambda: display_results(results))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
                finally:
                    self.after(0, lambda: self._update_status("Analysis complete"))
            
            threading.Thread(target=analyze_thread, daemon=True).start()
        
        def display_results(results):
            self.disk_results.delete("1.0", "end")
            
            if 'error' in results:
                self.disk_results.insert("1.0", f"Error: {results['error']}")
                return
            
            self.disk_results.insert("end", f"Total Size: {format_size(results['total_size'])}\n")
            self.disk_results.insert("end", f"Files: {results['file_count']}\n")
            self.disk_results.insert("end", f"Directories: {results['directory_count']}\n")
            
            if results.get('largest_files'):
                self.disk_results.insert("end", "\n=== TOP 10 LARGEST FILES ===\n")
                for item in results['largest_files'][:10]:
                    self.disk_results.insert("end", 
                        f"{format_size(item['size']):>10}  {item['name']}\n")
        
        analyze_btn = ctk.CTkButton(
            self.main_frame,
            text="🔍 Analyze",
            command=analyze,
            width=150,
            height=40
        )
        analyze_btn.pack(pady=20)
    
    # ============================================
    # Duplicate Finder View
    # ============================================
    
    def _show_duplicate_finder(self):
        """Display the duplicate finder view"""
        self._clear_main_frame()
        
        title = ctk.CTkLabel(
            self.main_frame,
            text="Duplicate Finder",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Find and remove duplicate files to free up space",
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        subtitle.pack(pady=(0, 20))
        
        # Path selection
        select_frame = ctk.CTkFrame(self.main_frame)
        select_frame.pack(fill="x", padx=30, pady=10)
        
        path_var = StringVar(value=os.path.expanduser('~'))
        
        ctk.CTkLabel(select_frame, text="Search Directory:").pack(pady=5)
        path_entry = ctk.CTkEntry(select_frame, textvariable=path_var)
        path_entry.pack(fill="x", padx=20)
        
        def browse():
            directory = filedialog.askdirectory()
            if directory:
                path_var.set(directory)
        
        ctk.CTkButton(select_frame, text="Browse", command=browse, width=100).pack(
            pady=10, padx=20, anchor="w")
        
        # Results area
        self.dup_results = ctk.CTkTextbox(self.main_frame, height=200)
        self.dup_results.pack(fill="both", expand=True, padx=30, pady=10)
        self.dup_results.insert("1.0", "Duplicate search results will appear here...")
        
        # Search button
        def search():
            path = path_var.get()
            if not os.path.exists(path):
                messagebox.showerror("Error", "Path does not exist!")
                return
            
            self._update_status("Searching for duplicates...", show_progress=True)
            
            def search_thread():
                results = self.duplicate_finder.find_duplicates([path])
                self.after(0, lambda: display_results(results))
            
            threading.Thread(target=search_thread, daemon=True).start()
        
        def display_results(results):
            self.dup_results.delete("1.0", "end")
            groups = results.get('groups', {})
            wasted = results.get('wasted_space', 0)
            
            self.dup_results.insert("end", f"Found {len(groups)} duplicate groups\n")
            self.dup_results.insert("end", f"Wasted space: {format_size(wasted)}\n")
            self.dup_results.insert("end", "\n")
            
            for i, (file_hash, files) in enumerate(list(groups.items())[:10], 1):
                if len(files) > 1:
                    self.dup_results.insert("end", f"Group {i}: {len(files)} files\n")
                    for f in files[:3]:
                        self.dup_results.insert("end", f"  - {f}\n")
                    if len(files) > 3:
                        self.dup_results.insert("end", f"  ... and {len(files)-3} more\n")
                    self.dup_results.insert("end", "\n")
            
            self._update_status(f"Found {len(groups)} duplicate groups")
        
        ctk.CTkButton(
            self.main_frame,
            text="🔍 Search",
            command=search,
            width=150,
            height=40
        ).pack(pady=20)
    
    # ============================================
    # Secure Delete View
    # ============================================
    
    def _show_secure_delete(self):
        """Display the secure delete view"""
        self._clear_main_frame()
        
        title = ctk.CTkLabel(
            self.main_frame,
            text="Secure File Deletion",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        warning = ctk.CTkLabel(
            self.main_frame,
            text="⚠️ WARNING: Securely deleted files CANNOT be recovered!",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="red"
        )
        warning.pack(pady=20)
        
        # File selection
        select_frame = ctk.CTkFrame(self.main_frame)
        select_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(select_frame, text="Select file to delete:").pack(pady=10)
        
        file_var = StringVar()
        file_entry = ctk.CTkEntry(select_frame, textvariable=file_var, height=35)
        file_entry.pack(fill="x", padx=20, pady=5)
        
        def browse():
            filename = filedialog.askopenfilename()
            if filename:
                file_var.set(filename)
        
        ctk.CTkButton(select_frame, text="Browse", command=browse).pack(
            pady=10, padx=20, anchor="w")
        
        # Passes selection
        passes_var = IntVar(value=3)
        ctk.CTkLabel(select_frame, text="Overwrite passes:").pack(pady=5)
        passes_slider = ctk.CTkSlider(
            select_frame,
            from_=1,
            to=7,
            number_of_steps=6,
            variable=passes_var
        )
        passes_slider.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(select_frame, textvariable=passes_var).pack(pady=5)
        
        # Delete button
        def delete():
            filepath = file_var.get()
            if not filepath or not os.path.exists(filepath):
                messagebox.showerror("Error", "File does not exist!")
                return
            
            passes = passes_var.get()
            
            proceed = messagebox.askyesno(
                "CONFIRM DELETION",
                f"Permanently delete:\n{filepath}\n\nPasses: {passes}\n\nThis CANNOT be undone!"
            )
            
            if proceed:
                self._update_status("Securely deleting...", show_progress=True)
                
                def delete_thread():
                    success = secure_delete(filepath, passes)
                    self.after(0, lambda: self._after_secure_delete(success))
                
                threading.Thread(target=delete_thread, daemon=True).start()
        
        def _after_secure_delete(success):
            if success:
                messagebox.showinfo("Success", "File securely deleted")
                self._update_status("File deleted")
            else:
                messagebox.showerror("Error", "Failed to delete file")
                self._update_status("Deletion failed")
        
        delete_btn = ctk.CTkButton(
            self.main_frame,
            text="🗑️ Secure Delete",
            command=delete,
            fg_color="red",
            hover_color="darkred",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        delete_btn.pack(pady=30)
    
    # ============================================
    # Settings View
    # ============================================
    
    def _show_settings(self):
        """Display settings view"""
        self._clear_main_frame()
        
        title = ctk.CTkLabel(
            self.main_frame,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", padx=30, pady=20)
        
        # Appearance
        ctk.CTkLabel(
            settings_frame,
            text="Appearance",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15, padx=20, anchor="w")
        
        appearance_var = StringVar(value="dark")
        
        ctk.CTkRadioButton(
            settings_frame,
            text="Dark Mode",
            variable=appearance_var,
            value="dark",
            command=lambda: ctk.set_appearance_mode("dark")
        ).pack(pady=5, padx=30, anchor="w")
        
        ctk.CTkRadioButton(
            settings_frame,
            text="Light Mode",
            variable=appearance_var,
            value="light",
            command=lambda: ctk.set_appearance_mode("light")
        ).pack(pady=5, padx=30, anchor="w")
        
        ctk.CTkRadioButton(
            settings_frame,
            text="System",
            variable=appearance_var,
            value="system",
            command=lambda: ctk.set_appearance_mode("system")
        ).pack(pady=5, padx=30, anchor="w")
        
        # Color theme
        ctk.CTkLabel(
            settings_frame,
            text="Color Theme",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15, padx=20, anchor="w")
        
        color_var = StringVar(value="blue")
        
        for color in ["blue", "green", "dark-blue"]:
            ctk.CTkRadioButton(
                settings_frame,
                text=color.title(),
                variable=color_var,
                value=color,
                command=lambda c=color: ctk.set_default_color_theme(c)
            ).pack(pady=5, padx=30, anchor="w")
        
        # Admin status
        ctk.CTkLabel(
            settings_frame,
            text="System",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15, padx=20, anchor="w")
        
        admin_text = "Running with Admin privileges" if is_admin() else "Limited mode - some features restricted"
        ctk.CTkLabel(
            settings_frame,
            text=admin_text,
            text_color="green" if is_admin() else "orange"
        ).pack(pady=5, padx=30, anchor="w")


# ============================================
# Main Entry Point
# ============================================

def main():
    """Main entry point"""
    app = CCleanerApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())