"""
Main Window UI with modern dark theme and professional layout
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QFrame, QLabel, QPushButton,
    QProgressBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QGuiApplication

# Add both desktop_app and project root to path
desktop_dir = Path(__file__).parent
project_root = desktop_dir.parent.parent
sys.path.insert(0, str(desktop_dir))  # For desktop_app modules
sys.path.insert(0, str(project_root)) # For original utils

# Import components 
from ui.components import (
    ProductDataTable, LogViewer, StatusPanel, 
    ActionButton, ModernProgressBar
)
from ui.styles import DraculaTheme
from controllers.scraping_controller import ScrapingController
from controllers.database_controller import DatabaseController



class MainWindow(QMainWindow):
    """Main application window with professional dark theme"""
    
    # Custom signals
    scraping_started = pyqtSignal()
    scraping_finished = pyqtSignal()
    retake_started = pyqtSignal()
    retake_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Logger ni oldindan yaratish
        try:
            from utils.log_config import get_logger
            self.logger = get_logger("main_window", "app.log")
        except ImportError:
            # Fallback logging
            import logging
            self.logger = logging.getLogger("main_window")

        # Initialize controllers
        try:
            self.scraping_controller = ScrapingController()
            self.db_controller = DatabaseController()
            print("✅ Controllers initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing controllers: {e}")
            # Show error dialog but continue
            QMessageBox.critical(
                None, 
                "Initialization Error", 
                f"Failed to initialize controllers:\n{e}\n\nSome features may not work."
            )
            self.scraping_controller = None
            self.db_controller = None
        
        # UI refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(10000)  # Refresh every 5 seconds
        
        self.setup_ui()
        self.connect_signals()
        self.load_initial_data()
    
    def setup_ui(self):

        # Ekran o‘lchamini olish
        screen = QGuiApplication.primaryScreen()
        size = screen.availableGeometry()

        """Initialize and setup the user interface"""
        self.setWindowTitle("1688 Product Scraper - Professional Edition")
        self.setGeometry(size)
        self.setMinimumSize(1200, 800)
        
        # Apply Dracula theme
        self.setStyleSheet(DraculaTheme.get_main_style())
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header section with controls
        self.create_header_section(main_layout)
        
        # Main content area with splitter
        self.create_main_content(main_layout)
        
        # Status bar
        self.create_status_bar()
    
    def create_header_section(self, parent_layout):
        """Create header with action buttons and status"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet(DraculaTheme.get_header_style())
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title_label = QLabel("1688 Product Scraper")
        title_label.setStyleSheet(DraculaTheme.get_title_style())
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        
        # Action buttons
        self.take_new_btn = ActionButton("Take New Products", "success")
        self.retake_btn = ActionButton("Retake Failed (404)", "warning")
        self.stop_btn = ActionButton("Stop Process", "danger")
        self.stop_btn.setEnabled(False)
        
        # Status indicators
        self.status_panel = StatusPanel()
        
        # Progress bar
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setVisible(False)
        
        # Layout
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.take_new_btn)
        header_layout.addWidget(self.retake_btn)
        header_layout.addWidget(self.stop_btn)
        header_layout.addWidget(self.status_panel)
        
        parent_layout.addWidget(header_frame)
        
        # Progress bar in separate row
        progress_frame = QFrame()
        progress_frame.setFixedHeight(40)
        progress_frame.setStyleSheet("background-color: #282a36; border-bottom: 1px solid #44475a;")
        progress_layout = QHBoxLayout(progress_frame)
        progress_layout.setContentsMargins(20, 5, 20, 5)
        progress_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(progress_frame)
    
    def create_main_content(self, parent_layout):
        """Create main content area with data table and logs"""
        # Main splitter for content areas
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet(DraculaTheme.get_splitter_style())
        
        # Left panel - Product Data Table
        left_panel = self.create_data_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Logs
        right_panel = self.create_logs_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions (70% table, 30% logs)
        main_splitter.setSizes([1000, 400])
        main_splitter.setCollapsible(0, False)
        main_splitter.setCollapsible(1, False)
        
        parent_layout.addWidget(main_splitter)
    
    def create_data_panel(self):
        """Create left panel with product data table"""
        panel = QFrame()
        panel.setStyleSheet(DraculaTheme.get_panel_style())
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel header
        header_label = QLabel("Product Data - Real-time Updates")
        header_label.setStyleSheet(DraculaTheme.get_panel_header_style())
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        # Create product data table
        self.product_table = ProductDataTable()
        
        layout.addWidget(header_label)
        layout.addWidget(self.product_table)
        
        return panel
    
    def create_logs_panel(self):
        """Create right panel with logs"""
        panel = QFrame()
        panel.setStyleSheet(DraculaTheme.get_panel_style())
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel header
        header_label = QLabel("System Logs - Live Feed")
        header_label.setStyleSheet(DraculaTheme.get_panel_header_style())
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        # Create log viewer
        self.log_viewer = LogViewer()
        
        layout.addWidget(header_label)
        layout.addWidget(self.log_viewer)
        
        return panel
    
    def create_status_bar(self):
        """Create status bar with connection and process info"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(DraculaTheme.get_status_bar_style())
        
        # Default status message
        if self.db_controller:
            self.status_bar.showMessage("✅ Ready - Database connected")
        else:
            self.status_bar.showMessage("⚠️ Warning - Database connection failed")
        
        self.setStatusBar(self.status_bar)
    
    def connect_signals(self):
        """Connect signals to their respective slots"""
        # Button signals
        self.take_new_btn.clicked.connect(self.start_new_scraping)
        self.retake_btn.clicked.connect(self.start_retake_process)
        self.stop_btn.clicked.connect(self.stop_current_process)
        
        # Controller signals (if available)
        if self.scraping_controller:
            self.scraping_controller.process_started.connect(self.on_process_started)
            self.scraping_controller.process_finished.connect(self.on_process_finished)
            self.scraping_controller.progress_updated.connect(self.on_progress_updated)
            self.scraping_controller.status_updated.connect(self.on_status_updated)
            self.scraping_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_initial_data(self):
        """Load initial data when application starts"""
        try:
            if self.db_controller:
                # Load product data
                self.refresh_product_data()
                
                # Get statistics
                stats = self.db_controller.get_processing_stats()
                total_products = stats.get('total_products', 0)
                failed_products = stats.get('failed', 0)
                scraped_products = stats.get('scraped', 0)
                
                self.status_panel.update_status(
                    total_products=total_products,
                    failed_products=failed_products,
                    scraped_products=scraped_products,
                    is_processing=False
                )
            else:
                # Show demo data
                self.status_panel.update_status(
                    total_products=0,
                    failed_products=0,
                    scraped_products=0,
                    is_processing=False
                )
                
        except Exception as e:
            self.show_error_message("Failed to load initial data", str(e))
    
    def refresh_data(self):
        """Refresh data periodically"""
        if self.scraping_controller and self.scraping_controller.is_processing():
            try:
                # Refresh table data
                self.refresh_product_data()
                
                # Update status panel
                if self.db_controller:
                    stats = self.db_controller.get_processing_stats()
                    # Map stats to expected parameters
                    self.status_panel.update_status(
                        total_products=stats.get('total_products', 0),
                        failed_products=stats.get('failed', 0),
                        scraped_products=stats.get('scraped', 0),
                        is_processing=stats.get('is_processing', False)
                    )
                
                # Refresh logs
                self.log_viewer.refresh_logs()
                
            except Exception as e:
                print(f"Error refreshing data: {e}")
        else:
            # Refresh table even when not processing
            try:
                self.refresh_product_data()
                
                if self.db_controller:
                    stats = self.db_controller.get_processing_stats()
                    self.status_panel.update_status(
                        total_products=stats.get('total_products', 0),
                        failed_products=stats.get('failed', 0),
                        scraped_products=stats.get('scraped', 0),
                        is_processing=False
                    )
            except Exception as e:
                print(f"Error refreshing data: {e}")
    
    def refresh_product_data(self):
        """Refresh product data table"""
        try:
            if self.db_controller:
                products = self.db_controller.get_products_for_display()
                self.product_table.update_data(products)
        except Exception as e:
            print(f"Error refreshing product data: {e}")
    
    def start_new_scraping(self):
        """Start new product scraping process"""
        if not self.scraping_controller:
            self.show_error_message("Controller Error", "Scraping controller not available")
            return
            
        reply = QMessageBox.question(
            self, 
            "Confirm New Scraping",
            "This will start scraping new products from 1688.\n\n"
            "The process may take several hours to complete.\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scraping_controller.start_new_scraping()
    
    def start_retake_process(self):
        """Start retake process for failed products"""
        if not self.scraping_controller or not self.db_controller:
            self.show_error_message("Controller Error", "Controllers not available")
            return
            
        failed_products = self.db_controller.get_failed_products()
        
        if not failed_products:
            QMessageBox.information(
                self,
                "No Failed Products",
                "There are no products with '404' status to retake."
            )
            return
        
        # Show retake selection dialog
        from ui.components import RetakeDialog
        retake_dialog = RetakeDialog(failed_products, self)
        retake_dialog.products_selected.connect(self._start_retake_for_selected)
        retake_dialog.show()
    
    def stop_current_process(self):
        """Stop current scraping process"""
        if not self.scraping_controller:
            return
            
        reply = QMessageBox.question(
            self,
            "Stop Process",
            "Are you sure you want to stop the current process?\n\n"
            "This will interrupt the scraping operation.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scraping_controller.stop_process()
    
    def on_process_started(self, process_type):
        """Handle process started signal"""
        self.take_new_btn.setEnabled(False)
        self.retake_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        self.status_bar.showMessage(f"🔄 {process_type} process started...")
        self.status_panel.set_processing(True)
    
    def on_process_finished(self, process_type, success):
        """Handle process finished signal"""
        self.take_new_btn.setEnabled(True)
        self.retake_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        status_icon = "✅" if success else "❌"
        status_text = "completed successfully" if success else "failed"
        
        self.status_bar.showMessage(f"{status_icon} {process_type} process {status_text}")
        self.status_panel.set_processing(False)
        
        # Refresh data after process completion
        self.refresh_product_data()
    
    def on_progress_updated(self, current, total, message):
        """Handle progress update signal"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{message} ({current}/{total})")
        else:
            self.progress_bar.setFormat(message)
    
    def on_status_updated(self, message):
        """Handle status update signal"""
        self.status_bar.showMessage(message)
    
    def on_error_occurred(self, error_message):
        """Handle error signal"""
        self.show_error_message("Process Error", error_message)
    
    def show_error_message(self, title, message):
        """Show error message to user"""
        QMessageBox.critical(
            self,
            title,
            f"An error occurred:\n\n{message}",
            QMessageBox.StandardButton.Ok
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            if self.scraping_controller and self.scraping_controller.is_processing():
                reply = QMessageBox.question(
                    self,
                    "Close Application",
                    "A scraping process is currently running.\n\n"
                    "Do you want to stop the process and close?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
                
                # Gracefully stop the process
                self.scraping_controller.stop_process()
                
                # Wait a bit for cleanup
                import time
                time.sleep(1)
            
            # Stop the refresh timer
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            
            # Cleanup controllers
            if hasattr(self, 'scraping_controller'):
                self.scraping_controller.cleanup()
            
            self.logger.info("Application closing gracefully")
            event.accept()
            
        except Exception as e:
            print(f"Error during close: {e}")
            # Force accept even with errors
            event.accept()
    
    def _start_retake_for_selected(self, selected_products):
        """Start retake process for selected products"""
        if not selected_products:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Retake Process",
            f"Selected {len(selected_products)} products for retake.\n\n"
            "This will reset their status and retry scraping.\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Start retake for selected products
            self.scraping_controller.start_retake_process(selected_products)