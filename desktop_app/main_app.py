#!/usr/bin/env python3
"""
1688 Scraper Desktop Application
Main application entry point with PyQt6 interface
"""

import sys
import os
from pathlib import Path

# ⭐ MUHIM: Path larni to'g'ri sozlash
current_dir = Path(__file__).parent          # desktop_app/
project_root = current_dir.parent            # 1688/

# Python path ga qo'shish
sys.path.insert(0, str(current_dir))        # desktop_app/ ni qo'shish
sys.path.insert(0, str(project_root))       # 1688/ ni qo'shish

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Endi import qilish
from ui.main_window import MainWindow


class ScrapingApplication(QApplication):
    """Main application class with custom styling and configuration"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setup_application()
    
    def setup_application(self):
        """Configure application properties and styling"""
        self.setApplicationName("1688 Product Scraper")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Your Company")
        
        # PyQt6 da High DPI scaling avtomatik yoqilgan
        # AA_EnableHighDpiScaling va AA_UseHighDpiPixmaps kerak emas
        
        # Set application icon if exists
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))


def main():
    """Main application entry point"""
    # PyQt6 da High DPI avtomatik yoqilgan, manual o'rnatish kerak emas
    
    try:
        app = ScrapingApplication(sys.argv)
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        # Start application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()