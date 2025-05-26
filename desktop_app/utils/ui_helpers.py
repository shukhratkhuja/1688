"""
UI Helper Functions and Utilities
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices

# Add project root to Python path
desktop_dir = Path(__file__).parent
project_root = desktop_dir.parent.parent
sys.path.insert(0, str(project_root)) # For original utils


from utils.log_config import get_logger


class UIHelpers:
    """Collection of UI helper functions"""
    
    @staticmethod
    def show_success_message(parent, title: str, message: str):
        """Show success message dialog"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_error_message(parent, title: str, message: str, details: str = None):
        """Show error message dialog with optional details"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setDetailedText(details)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_warning_message(parent, title: str, message: str):
        """Show warning message dialog"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def confirm_action(parent, title: str, message: str, details: str = None) -> bool:
        """Show confirmation dialog and return user choice"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setInformativeText(details)
        
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        return msg_box.exec() == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def get_user_input(parent, title: str, prompt: str, default_text: str = "") -> Optional[str]:
        """Get text input from user"""
        text, ok = QInputDialog.getText(parent, title, prompt, text=default_text)
        return text if ok else None
    
    @staticmethod
    def select_file(parent, title: str, filters: str = "All Files (*)") -> Optional[str]:
        """Open file selection dialog"""
        file_path, _ = QFileDialog.getOpenFileName(parent, title, "", filters)
        return file_path if file_path else None
    
    @staticmethod
    def select_directory(parent, title: str) -> Optional[str]:
        """Open directory selection dialog"""
        dir_path = QFileDialog.getExistingDirectory(parent, title)
        return dir_path if dir_path else None
    
    @staticmethod
    def open_file_location(file_path: str):
        """Open file location in system file manager"""
        try:
            path = Path(file_path)
            if path.exists():
                if sys.platform == "win32":
                    os.startfile(path.parent)
                elif sys.platform == "darwin":
                    os.system(f"open '{path.parent}'")
                else:
                    os.system(f"xdg-open '{path.parent}'")
        except Exception as e:
            print(f"Error opening file location: {e}")
    
    @staticmethod
    def open_url(url: str):
        """Open URL in default browser"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"Error opening URL: {e}")
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        """Format timestamp to readable date/time"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Unknown"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text with ellipsis if too long"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Basic URL validation"""
        return url.startswith(('http://', 'https://')) and len(url) > 10


class NotificationManager(QObject):
    """Manager for showing system notifications and status updates"""
    
    notification_requested = pyqtSignal(str, str, str)  # title, message, type
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("notification_manager", "app.log")
    
    def show_info(self, title: str, message: str):
        """Show info notification"""
        self.notification_requested.emit(title, message, "info")
        self.logger.info(f"Notification: {title} - {message}")
    
    def show_success(self, title: str, message: str):
        """Show success notification"""
        self.notification_requested.emit(title, message, "success")
        self.logger.info(f"Success: {title} - {message}")
    
    def show_warning(self, title: str, message: str):
        """Show warning notification"""
        self.notification_requested.emit(title, message, "warning")
        self.logger.warning(f"Warning: {title} - {message}")
    
    def show_error(self, title: str, message: str):
        """Show error notification"""
        self.notification_requested.emit(title, message, "error")
        self.logger.error(f"Error: {title} - {message}")


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.logger = get_logger("performance_monitor", "app.log")
        self.start_time = datetime.now()
        self.metrics = {
            'ui_updates': 0,
            'database_queries': 0,
            'errors': 0,
            'memory_warnings': 0
        }
    
    def record_ui_update(self):
        """Record UI update event"""
        self.metrics['ui_updates'] += 1
    
    def record_database_query(self):
        """Record database query event"""
        self.metrics['database_queries'] += 1
    
    def record_error(self):
        """Record error event"""
        self.metrics['errors'] += 1
    
    def record_memory_warning(self):
        """Record memory warning event"""
        self.metrics['memory_warnings'] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': UIHelpers.format_duration(int(uptime.total_seconds())),
            'metrics': self.metrics.copy(),
            'ui_updates_per_minute': self.metrics['ui_updates'] / max(uptime.total_seconds() / 60, 1),
            'database_queries_per_minute': self.metrics['database_queries'] / max(uptime.total_seconds() / 60, 1)
        }


class ConfigManager:
    """Manager for application configuration"""
    
    def __init__(self, config_file: str = "desktop_app_config.json"):
        self.config_file = Path(config_file)
        self.logger = get_logger("config_manager", "app.log")
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'window': {
                'width': 1400,
                'height': 900,
                'maximized': False
            },
            'refresh': {
                'table_interval': 2000,
                'log_interval': 1000,
                'progress_interval': 3000
            },
            'ui': {
                'theme': 'dracula',
                'log_max_lines': 1000,
                'table_max_rows': 1000
            },
            'notifications': {
                'show_success': True,
                'show_warnings': True,
                'show_errors': True
            }
        }
        
        if not self.config_file.exists():
            self._save_config(default_config)
            return default_config
        
        try:
            import json
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            # Merge with defaults to ensure all keys exist
            merged_config = self._merge_configs(default_config, loaded_config)
            return merged_config
            
        except Exception as e:
            self.logger.warning(f"Failed to load config, using defaults: {e}")
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'window.width')"""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self._config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set value
        config[keys[-1]] = value
        
        # Save to file
        self._save_config(self._config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()


class DataExporter:
    """Export application data to various formats"""
    
    def __init__(self, db_controller):
        self.db_controller = db_controller
        self.logger = get_logger("data_exporter", "app.log")
    
    def export_to_csv(self, file_path: str, data_type: str = "products") -> bool:
        """Export data to CSV file"""
        try:
            import csv
            
            if data_type == "products":
                data = self.db_controller.get_products_for_display()
                headers = [
                    "ID", "Product URL", "Title (Chinese)", "Title (English)",
                    "Scraped", "Translated", "Uploaded", "Notion Updated", "Created"
                ]
            elif data_type == "failed":
                data = self.db_controller.get_failed_products()
                headers = ["ID", "Product URL", "Title (Chinese)", "Created"]
            else:
                raise ValueError(f"Unknown data type: {data_type}")
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)
            
            self.logger.info(f"Successfully exported {len(data)} rows to {file_path}")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, f"exporting {data_type} to CSV")
            return False
    
    def export_stats_to_json(self, file_path: str) -> bool:
        """Export processing statistics to JSON"""
        try:
            import json
            
            stats = self.db_controller.get_processing_stats()
            db_info = self.db_controller.get_database_info()
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'processing_stats': stats,
                'database_info': db_info
            }
            
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully exported stats to {file_path}")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "exporting stats to JSON")
            return False


class UpdateChecker:
    """Check for application updates"""
    
    def __init__(self):
        self.logger = get_logger("update_checker", "app.log")
        self.current_version = "1.0.0"
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates"""
        try:
            # This would typically check a remote server or GitHub releases
            # For now, return a mock response
            return {
                'update_available': False,
                'current_version': self.current_version,
                'latest_version': self.current_version,
                'download_url': None,
                'release_notes': None
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to check for updates: {e}")
            return {
                'update_available': False,
                'current_version': self.current_version,
                'latest_version': None,
                'download_url': None,
                'release_notes': None,
                'error': str(e)
            }


class KeyboardShortcuts:
    """Define and manage keyboard shortcuts"""
    
    SHORTCUTS = {
        'start_scraping': 'Ctrl+N',
        'stop_process': 'Ctrl+S',
        'retake_failed': 'Ctrl+R',
        'refresh_data': 'F5',
        'export_data': 'Ctrl+E',
        'show_logs': 'Ctrl+L',
        'show_stats': 'Ctrl+I',
        'quit_app': 'Ctrl+Q'
    }
    
    @classmethod
    def get_shortcut(cls, action: str) -> str:
        """Get keyboard shortcut for action"""
        return cls.SHORTCUTS.get(action, "")
    
    @classmethod
    def get_all_shortcuts(cls) -> Dict[str, str]:
        """Get all keyboard shortcuts"""
        return cls.SHORTCUTS.copy()


class ThemeManager:
    """Manage application themes"""
    
    def __init__(self):
        self.current_theme = "dracula"
        self.logger = get_logger("theme_manager", "app.log")
    
    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        return ["dracula", "light", "dark", "system"]
    
    def set_theme(self, theme_name: str) -> bool:
        """Set application theme"""
        try:
            available_themes = self.get_available_themes()
            if theme_name not in available_themes:
                raise ValueError(f"Unknown theme: {theme_name}")
            
            self.current_theme = theme_name
            self.logger.info(f"Theme changed to: {theme_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set theme: {e}")
            return False
    
    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme


class SystemTray:
    """System tray functionality (if supported)"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = get_logger("system_tray", "app.log")
        self.tray_icon = None
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
            from PyQt6.QtGui import QIcon, QAction
            
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return False
            
            # Create tray icon
            self.tray_icon = QSystemTrayIcon(self.main_window)
            
            # Set icon (you would need an actual icon file)
            # self.tray_icon.setIcon(QIcon("icon.png"))
            
            # Create context menu
            tray_menu = QMenu()
            
            show_action = QAction("Show Window", self.main_window)
            show_action.triggered.connect(self.main_window.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide Window", self.main_window)
            hide_action.triggered.connect(self.main_window.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self.main_window)
            quit_action.triggered.connect(self.main_window.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            self.logger.info("System tray icon created successfully")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to setup system tray: {e}")
            return False
    
    def show_message(self, title: str, message: str, icon_type="Information"):
        """Show tray notification"""
        if self.tray_icon:
            from PyQt6.QtWidgets import QSystemTrayIcon
            
            icon_map = {
                "Information": QSystemTrayIcon.MessageIcon.Information,
                "Warning": QSystemTrayIcon.MessageIcon.Warning,
                "Critical": QSystemTrayIcon.MessageIcon.Critical
            }
            
            self.tray_icon.showMessage(
                title, message, icon_map.get(icon_type, QSystemTrayIcon.MessageIcon.Information)
            )


class ApplicationInfo:
    """Application information and metadata"""
    
    APP_NAME = "1688 Product Scraper"
    VERSION = "1.0.0"
    AUTHOR = "Your Company"
    DESCRIPTION = "Professional desktop application for scraping and managing 1688 product data"
    
    @classmethod
    def get_about_text(cls) -> str:
        """Get formatted about text"""
        return f"""
        <h2>{cls.APP_NAME}</h2>
        <p><strong>Version:</strong> {cls.VERSION}</p>
        <p><strong>Author:</strong> {cls.AUTHOR}</p>
        <p><strong>Description:</strong><br>{cls.DESCRIPTION}</p>
        
        <p><strong>Features:</strong></p>
        <ul>
            <li>Real-time product data scraping from 1688</li>
            <li>Automatic translation and processing</li>
            <li>Google Drive integration</li>
            <li>Notion database updates</li>
            <li>Failed product retake functionality</li>
            <li>Professional dark theme interface</li>
            <li>Comprehensive logging and monitoring</li>
        </ul>
        
        <p><strong>System Requirements:</strong></p>
        <ul>
            <li>Python 3.8+</li>
            <li>PyQt6</li>
            <li>SQLite database support</li>
            <li>Internet connection for scraping</li>
        </ul>
        """
    
    @classmethod
    def get_system_info(cls) -> Dict[str, Any]:
        """Get system information"""
        import platform
        
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.VERSION,
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor() or "Unknown"
        }
