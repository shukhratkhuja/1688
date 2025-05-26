"""
Custom UI Components with modern styling
"""

import os, sys
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QTextEdit, QWidget, 
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QFrame, QHeaderView, QCheckBox,
    QAbstractItemView, QScrollArea, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette

# Add both desktop_app and project root to path
desktop_dir = Path(__file__).parent
project_root = desktop_dir.parent.parent
sys.path.insert(0, str(desktop_dir))  # For desktop_app modules
sys.path.insert(0, str(project_root)) # For original utils


from ui.styles import DraculaTheme



class ProductDataTable(QTableWidget):
    """Professional product data table with real-time updates"""
    
    # Define column headers and their order
    COLUMNS = [
        ("ID", 60),
        ("Product URL", 200),
        ("Title (Chinese)", 150),
        ("Title (English)", 150),
        ("Scraped", 80),
        ("Translated", 80),
        ("Uploaded to GD", 150),
        ("Updated on Notion", 150),
        ("Created", 120)
    ]
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        self.apply_styling()

    
    def copy_url_text(self, url_text):
        """Copy URL text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(url_text)
        
        # Success message (optional)
        print(f"URL copied: {url_text}")

    # ProductDataTable class ga yangi funksiyalar qo'shing:
    def show_context_menu(self, position):
        """Show context menu for table items"""
        item = self.itemAt(position)
        if item is None:
            return
        
        # Faqat URL column (column 1) uchun context menu
        if item.column() == 1:  # URL column
            # URL text ni oldindan oling
            url_text = item.text()  # BU MUHIM - oldindan oling
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #44475a;
                    color: #f8f8f2;
                    border: 1px solid #6272a4;
                    border-radius: 6px;
                    padding: 4px;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #bd93f9;
                    color: #282a36;
                }
            """)
            
            copy_action = menu.addAction("📋 Copy URL")
            # Lambda da item o'rniga url_text ishlatiladi
            copy_action.triggered.connect(lambda: self.copy_url_text(url_text))
            
            menu.exec(self.mapToGlobal(position))

    
    def setup_table(self):
        """Initialize table structure"""
        # Set column count and headers
        self.setColumnCount(len(self.COLUMNS))
        headers = [col[0] for col in self.COLUMNS]
        self.setHorizontalHeaderLabels(headers)

         # Context menu uchun
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths
        for i, (header, width) in enumerate(self.COLUMNS):
            self.setColumnWidth(i, width)
        
        # Table behavior
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSortingEnabled(True)
        
        # Header behavior
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # URL column stretches
        
        # Vertical header
        self.verticalHeader().setVisible(True)
    
    def apply_styling(self):

        """Apply Dracula theme styling"""
        self.setStyleSheet(DraculaTheme.get_table_style())



    def update_data(self, products_data):
        """Update table with new product data"""
        self.setRowCount(len(products_data))
        
        for row, product in enumerate(products_data):
            # Extract data from product tuple/dict
            if isinstance(product, (tuple, list)):
                product_id, url, title_chn, title_en, scraped, translated, uploaded, notion, created = product
            else:
                # Handle dict format if needed
                product_id = product.get('id', '')
                url = product.get('product_url', '')
                title_chn = product.get('title_chn', '')
                title_en = product.get('title_en', '')
                scraped = product.get('scraped_status', 0)
                translated = product.get('translated_status', 0)
                uploaded = product.get('uploaded_to_gd_status', 0)
                notion = product.get('updated_on_notion_status', 0)
                created = product.get('created_at', '')
            
            # Set cell values
            self.setItem(row, 0, self.create_id_cell(product_id))
            self.setItem(row, 1, self.create_url_cell(url))
            self.setItem(row, 2, self.create_cell_item(title_chn or ""))
            self.setItem(row, 3, self.create_cell_item(title_en or ""))
            self.setItem(row, 4, self.create_status_cell(scraped))
            self.setItem(row, 5, self.create_status_cell(translated))
            self.setItem(row, 6, self.create_status_cell(uploaded))
            self.setItem(row, 7, self.create_status_cell(notion))
            self.setItem(row, 8, self.create_cell_item(self.format_datetime(created)))
        
        # Sort by ID descending (newest first)
        self.sortItems(0, Qt.SortOrder.DescendingOrder)    


    def create_id_cell(self, product_id):
        """Create ID cell with proper numeric sorting"""
        item = QTableWidgetItem(str(product_id))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Numeric sort uchun integer value o'rnatish
        try:
            numeric_id = int(product_id) if product_id else 0
            item.setData(Qt.ItemDataRole.UserRole, numeric_id)
        except (ValueError, TypeError):
            item.setData(Qt.ItemDataRole.UserRole, 0)
        
        return item

    def create_cell_item(self, text, data_type="text"):
        """Create a standard table cell item with proper data type"""
        item = QTableWidgetItem(str(text))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Data type ga qarab sort qilish uchun data o'rnatish
        if data_type == "number":
            try:
                # Number sifatida sort qilish uchun
                item.setData(Qt.ItemDataRole.UserRole, int(text))
            except (ValueError, TypeError):
                item.setData(Qt.ItemDataRole.UserRole, 0)
        
        return item

    
    def create_url_cell(self, url):
        """Create URL cell with special formatting"""
        item = self.create_cell_item(url)
        # Highlight 404 URLs
        if "404" in str(url) or not url:
            item.setBackground(QColor("#ff5555"))
            item.setForeground(QColor("#ffffff"))
        return item
    
    def create_status_cell(self, status):
        """Create status cell with colored indicators"""
        status_text = "✅" if status else "⚪️"
        item = self.create_cell_item(status_text)
        
        # Color coding
        if status:
            item.setBackground(QColor("#50fa7b"))
            item.setForeground(QColor("#282a36"))
        else:
            item.setBackground(QColor("#ffb86c"))
            item.setForeground(QColor("#282a36"))
        
        return item
    
    def format_datetime(self, dt_str):
        """Format datetime string for display"""
        if not dt_str:
            return ""
        try:
            # Parse and format datetime
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%m/%d %H:%M")
        except:
            return str(dt_str)[:16]  # Fallback to first 16 chars


class LogViewer(QTextEdit):
    """Real-time log viewer with auto-scroll and syntax highlighting"""
    
    def __init__(self):
        super().__init__()
        self.log_file_path = "logs/app.log"
        self.last_position = 0
        
        self.setup_viewer()
        self.apply_styling()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(1000)  # Refresh every second
    
    def setup_viewer(self):
        """Initialize log viewer settings"""
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Load existing logs
        self.load_initial_logs()
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet(DraculaTheme.get_log_viewer_style())
    
    def load_initial_logs(self):
        """Load existing log content"""
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.setPlainText(content)
                self.last_position = len(content)
            
            # Yoki cursor usuli:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.setTextCursor(cursor)
                
         
    def refresh_logs(self):
        """Refresh logs with new content only"""
        if not os.path.exists(self.log_file_path):
            return
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                
                if new_content:
                    # Append new content with syntax highlighting
                    self.append_colored_log(new_content)
                    self.last_position = f.tell()
                    
                    # Auto-scroll to bottom
                    self.moveCursor(self.textCursor().End)
        except Exception as e:
            pass  # Silently handle file access errors
    
    def append_colored_log(self, text):
        """Add colored log text based on log level"""
        lines = text.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # Color based on log level
            if "ERROR" in line or "❌" in line:
                self.append(f'<span style="color: #ff5555;">{line}</span>')
            elif "WARNING" in line or "⚠️" in line:
                self.append(f'<span style="color: #ffb86c;">{line}</span>')
            elif "INFO" in line or "✅" in line:
                self.append(f'<span style="color: #50fa7b;">{line}</span>')
            elif "DEBUG" in line:
                self.append(f'<span style="color: #6272a4;">{line}</span>')
            else:
                self.append(f'<span style="color: #f8f8f2;">{line}</span>')


class StatusPanel(QWidget):
    """Status panel showing process statistics"""
    
    def __init__(self):
        super().__init__()
        self.setup_panel()
        self.apply_styling()
    
    def setup_panel(self):
        """Initialize status panel layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # Status indicators
        self.total_label = QLabel("Total: 0")
        self.scraped_label = QLabel("Scraped: 0")
        self.failed_label = QLabel("Failed: 0")
        self.processing_label = QLabel("●")
        
        # Styling for labels
        for label in [self.total_label, self.scraped_label, self.failed_label]:
            label.setFont(QFont("Segoe UI", 9))
        
        self.processing_label.setFont(QFont("Segoe UI", 12))
        
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.processing_label)
        layout.addWidget(self.total_label)
        layout.addWidget(self.scraped_label)
        layout.addWidget(self.failed_label)
    
    def apply_styling(self):
        """Apply styling to status panel"""
        self.setStyleSheet("""
            QWidget {
                color: #f8f8f2;
                background-color: transparent;
            }
            QLabel {
                color: #f8f8f2;
            }
        """)
    
    def update_status(self, total_products=0, failed_products=0, scraped_products=0, is_processing=False, **kwargs):
        """Update status panel information"""
        self.total_label.setText(f"Total: {total_products}")
        self.scraped_label.setText(f"Scraped: {scraped_products}")
        self.failed_label.setText(f"Failed: {failed_products}")
        
        # Processing indicator
        if is_processing:
            self.processing_label.setText("🔄")
            self.processing_label.setStyleSheet("color: #ffb86c;")
        else:
            self.processing_label.setText("●")
            self.processing_label.setStyleSheet("color: #50fa7b;")
    
    def set_processing(self, is_processing):
        """Set processing state"""
        if is_processing:
            self.processing_label.setText("🔄")
            self.processing_label.setStyleSheet("color: #ffb86c;")
        else:
            self.processing_label.setText("●")
            self.processing_label.setStyleSheet("color: #50fa7b;")


class ActionButton(QPushButton):
    """Custom styled action button"""
    
    def __init__(self, text, button_type="primary"):
        super().__init__(text)
        self.button_type = button_type
        self.setup_button()
        self.apply_styling()
    
    def setup_button(self):
        """Initialize button properties"""
        self.setMinimumHeight(35)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def apply_styling(self):
        """Apply button styling based on type"""
        base_style = """
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:pressed {
                opacity: 0.7;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """
        
        if self.button_type == "success":
            color_style = """
                QPushButton {
                    background-color: #50fa7b;
                    color: #282a36;
                }
                QPushButton:hover {
                    background-color: #5af78e;
                }
            """
        elif self.button_type == "warning":
            color_style = """
                QPushButton {
                    background-color: #ffb86c;
                    color: #282a36;
                }
                QPushButton:hover {
                    background-color: #ffc374;
                }
            """
        elif self.button_type == "danger":
            color_style = """
                QPushButton {
                    background-color: #ff5555;
                    color: #f8f8f2;
                }
                QPushButton:hover {
                    background-color: #ff6b6b;
                }
            """
        else:  # primary
            color_style = """
                QPushButton {
                    background-color: #bd93f9;
                    color: #282a36;
                }
                QPushButton:hover {
                    background-color: #c9a6fa;
                }
            """
        
        self.setStyleSheet(base_style + color_style)


class ModernProgressBar(QProgressBar):
    """Custom styled progress bar"""
    
    def __init__(self):
        super().__init__()
        self.setup_progress_bar()
        self.apply_styling()
    
    def setup_progress_bar(self):
        """Initialize progress bar"""
        self.setMinimumHeight(25)
        self.setMaximumHeight(25)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    
    def apply_styling(self):
        """Apply modern styling to progress bar"""
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #44475a;
                border-radius: 12px;
                background-color: #44475a;
                color: #f8f8f2;
                font-weight: bold;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #50fa7b, stop:1 #8be9fd
                );
                border-radius: 10px;
                margin: 2px;
            }
        """)


class RetakeDialog(QWidget):
    """Dialog for selecting products to retake"""
    
    products_selected = pyqtSignal(list)
    
    def __init__(self, failed_products, parent=None):
        super().__init__(parent)
        self.failed_products = failed_products
        self.selected_products = []
        
        # Window properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # For dragging functionality
        self.drag_position = None

        # Window state tracking
        self.is_maximized = False
        self.normal_geometry = None

        
        self.setup_dialog()
        self.apply_styling()
    
    def setup_dialog(self):
        """Initialize retake dialog"""
        self.setGeometry(200, 200, 1000, 700)
        
        # Main layout with background frame
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Background frame with shadow effect
        self.background_frame = QFrame()
        self.background_frame.setObjectName("backgroundFrame")
        self.background_frame.setStyleSheet("""
            QFrame#backgroundFrame {
                background-color: #282a36;
                border: 2px solid #44475a;
                border-radius: 12px;
            }
        """)
        
        # Shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.background_frame.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.background_frame)
        
        # Content layout inside background frame
        content_layout = QVBoxLayout(self.background_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Title bar with window controls
        self.create_title_bar(content_layout)
        
        # Content area
        self.create_content_area(content_layout)
    
    def create_title_bar(self, parent_layout):
        """Create custom title bar with drag and window controls"""
        title_bar = QFrame()
        title_bar.setFixedHeight(50)
        title_bar.setObjectName("titleBar")
        title_bar.setStyleSheet("""
            QFrame#titleBar {
                background-color: #44475a;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid #6272a4;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        # Icon and title
        title_icon = QLabel("🔄")
        title_icon.setFont(QFont("Segoe UI", 14))
        title_icon.setStyleSheet("color: #bd93f9;")
        
        title_text = QLabel("Retake Failed Products")
        title_text.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_text.setStyleSheet("color: #f8f8f2; background: transparent;")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        # Window control buttons
        self.create_window_controls(title_layout)
        
        parent_layout.addWidget(title_bar)
        
        # Make title bar draggable
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        title_bar.mouseReleaseEvent = self.title_bar_mouse_release
    
       
    # Window controls buttonlarni yangilang:
    def create_window_controls(self, layout):
        """Create minimize, maximize, close buttons"""
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #f8f8f2;
                font-size: 14px;
                font-weight: bold;
                width: 30px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #6272a4;
            }
            QPushButton:pressed {
                background-color: #44475a;
            }
        """
        
        close_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #f8f8f2;
                font-size: 14px;
                font-weight: bold;
                width: 30px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ff5555;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #ff4444;
            }
        """
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet(close_button_style)
        close_btn.clicked.connect(self.close)
        close_btn.setToolTip("Close")
        
        # Add buttons to layout
        layout.addWidget(close_btn)

        
    def create_content_area(self, parent_layout):
        """Create main content area"""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)
        
        # Header info
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #44475a;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        info_label = QLabel(f"Found {len(self.failed_products)} products with '404' status.\nSelect products you want to retake:")
        info_label.setFont(QFont("Segoe UI", 10))
        info_label.setStyleSheet("color: #f8f8f2; background: transparent; padding: 0;")
        header_layout.addWidget(info_label)
        content_layout.addWidget(header_frame)
        
        # Selection controls
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        select_all_btn = ActionButton("✅ Select All", "success")
        select_all_btn.setMaximumWidth(120)
        deselect_all_btn = ActionButton("❌ Deselect All", "warning") 
        deselect_all_btn.setMaximumWidth(120)
        
        selected_count_label = QLabel("Selected: 0")
        selected_count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        selected_count_label.setStyleSheet("color: #50fa7b;")
        self.selected_count_label = selected_count_label
        
        controls_layout.addWidget(select_all_btn)
        controls_layout.addWidget(deselect_all_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(selected_count_label)
        content_layout.addWidget(controls_frame)
        
        # Product selection table
        self.selection_table = QTableWidget()
        self.setup_selection_table()
        content_layout.addWidget(self.selection_table)
        
        # Action buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        retake_btn = ActionButton("Retake Selected", "success")
        retake_btn.setMinimumHeight(40)
        cancel_btn = ActionButton("Cancel", "danger")
        cancel_btn.setMinimumHeight(40)
        
        button_layout.addStretch()
        button_layout.addWidget(retake_btn)
        button_layout.addWidget(cancel_btn)
        content_layout.addWidget(button_frame)
        
        parent_layout.addWidget(content_widget)
        
        # Connect signals
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn.clicked.connect(self.deselect_all)
        retake_btn.clicked.connect(self.retake_selected)
        cancel_btn.clicked.connect(self.close)
        
        # Connect table selection changes
        # self.selection_table.itemChanged.connect(self.update_selected_count)
    
    # Title bar drag functionality
    def title_bar_mouse_press(self, event):
        """Handle title bar mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def title_bar_mouse_move(self, event):
        """Handle title bar mouse move for dragging"""
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            self.drag_position is not None):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    

    def title_bar_mouse_release(self, event):
        """Handle title bar mouse release"""
        self.drag_position = None


    # RetakeDialog class ga qo'shing:
    def show_retake_context_menu(self, position):
        """Show context menu for retake table items"""
        item = self.selection_table.itemAt(position)
        if item is None:
            return
        
        # Faqat URL column (column 2) uchun context menu
        if item.column() == 2:  # URL column in retake dialog
            # URL text ni oldindan oling
            url_text = item.text()  # BU MUHIM
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #44475a;
                    color: #f8f8f2;
                    border: 1px solid #6272a4;
                    border-radius: 6px;
                    padding: 4px;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #bd93f9;
                    color: #282a36;
                }
            """)
            
            copy_action = menu.addAction("📋 Copy URL")
            # url_text ishlatiladi, item emas
            copy_action.triggered.connect(lambda: self.copy_retake_url_text(url_text))
            
            menu.exec(self.selection_table.mapToGlobal(position))


    def copy_retake_url_text(self, url_text):
        """Copy URL text to clipboard from retake table"""
        from PyQt6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(url_text)
        
        print(f"URL copied: {url_text}")

    
    def setup_selection_table(self):
        """Setup the product selection table"""
        headers = ["Select", "ID", "Product URL", "Title (Chinese)", "Created Date"]
        self.selection_table.setColumnCount(len(headers))
        self.selection_table.setHorizontalHeaderLabels(headers)
        self.selection_table.setRowCount(len(self.failed_products))

        # Context menu uchun
        self.selection_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.selection_table.customContextMenuRequested.connect(self.show_retake_context_menu)

        
        # Table styling
        self.selection_table.setAlternatingRowColors(True)
        self.selection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.selection_table.verticalHeader().setVisible(False)
        
        # Set column widths
        self.selection_table.setColumnWidth(0, 80)   # Checkbox
        self.selection_table.setColumnWidth(1, 60)   # ID
        self.selection_table.setColumnWidth(2, 300)  # URL
        self.selection_table.setColumnWidth(3, 250)  # Title
        
        # Header stretch
        header = self.selection_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # Populate table with failed products
        for row, product in enumerate(self.failed_products):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(False)  # Select all by default
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                    font-size: 10pt;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #6272a4;
                    border-radius: 3px;
                    background-color: #282a36;
                }
                QCheckBox::indicator:checked {
                    background-color: #50fa7b;
                    border-color: #50fa7b;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0iIzI4MmEzNiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                }
                QCheckBox::indicator:hover {
                    border-color: #bd93f9;
                }
            """)
            
            checkbox.stateChanged.connect(self.update_selected_count)
            # Center checkbox in cell
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            

            self.selection_table.setCellWidget(row, 0, checkbox_widget)
            # Product data
            product_id = str(product[0]) if product[0] else "N/A"
            product_url = product[1] if len(product) > 1 else "N/A"
            title_chn = product[2] if len(product) > 2 and product[2] else "404 Error"
            created_at = product[3] if len(product) > 3 and product[3] else "Unknown"
            
            # Format created date
            try:
                from datetime import datetime
                if created_at and created_at != "Unknown":
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
            
            # Create table items
            id_item = QTableWidgetItem(product_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            url_item = QTableWidgetItem(product_url)
            url_item.setFlags(url_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            url_item.setToolTip(product_url)
            
            title_item = QTableWidgetItem(title_chn)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            title_item.setBackground(QColor("#ff5555"))  # Red background for 404
            title_item.setForeground(QColor("#ffffff"))
            
            date_item = QTableWidgetItem(created_at)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.selection_table.setItem(row, 1, id_item)
            self.selection_table.setItem(row, 2, url_item)
            self.selection_table.setItem(row, 3, title_item)
            self.selection_table.setItem(row, 4, date_item)
        
        # Update selected count initially
        self.update_selected_count()
    
    def apply_styling(self):
        """Apply dialog styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #f8f8f2;
                font-family: 'Segoe UI';
            }
            
            QTableWidget {
                background-color: #282a36;
                color: #f8f8f2;
                gridline-color: #44475a;
                border: 1px solid #44475a;
                border-radius: 6px;
                selection-background-color: #bd93f9;
                selection-color: #282a36;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #44475a;
            }
            
            QTableWidget::item:selected {
                background-color: #bd93f9;
                color: #282a36;
            }
            
            QTableWidget::item:alternate {
                background-color: rgba(68, 71, 90, 0.3);
            }
            
            QHeaderView::section {
                background-color: #44475a;
                color: #f8f8f2;
                padding: 10px;
                border: none;
                border-right: 1px solid #282a36;
                font-weight: bold;
            }
            
            QHeaderView::section:hover {
                background-color: #6272a4;
            }
        """)
    
    def select_all(self):
        for row in range(self.selection_table.rowCount()):
            checkbox_widget = self.selection_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(True)
                    checkbox.blockSignals(False)
        self.update_selected_count()  # Manual call
    
    def deselect_all(self):
        for row in range(self.selection_table.rowCount()):
            checkbox_widget = self.selection_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
        self.update_selected_count()  # Manual call
    
    def update_selected_count(self):
        """Update selected products count"""
        selected_count = 0
        for row in range(self.selection_table.rowCount()):
            checkbox_widget = self.selection_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_count += 1
        
        self.selected_count_label.setText(f"Selected: {selected_count}")
        
        # Change color based on selection
        if selected_count == 0:
            self.selected_count_label.setStyleSheet("color: #ff5555;")  # Red
        elif selected_count == len(self.failed_products):
            self.selected_count_label.setStyleSheet("color: #50fa7b;")  # Green
        else:
            self.selected_count_label.setStyleSheet("color: #ffb86c;")  # Orange
    
    def retake_selected(self):
        """Get selected products and emit signal"""
        selected = []
        for row in range(self.selection_table.rowCount()):
            checkbox_widget = self.selection_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected.append(self.failed_products[row])
        
        if not selected:
            QMessageBox.warning(
                self, 
                "No Selection", 
                "Please select at least one product to retake."
            )
            return
        
        # Emit signal with selected products
        self.products_selected.emit(selected)
        self.close()

class DatabaseStatsWidget(QFrame):
    """Widget showing database statistics"""
    
    def __init__(self):
        super().__init__()
        self.setup_widget()
        self.apply_styling()
    
    def setup_widget(self):
        """Initialize stats widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Title
        title = QLabel("📊 Database Statistics")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Stats labels
        self.total_products_label = QLabel("Total Products: 0")
        self.scraped_label = QLabel("Scraped: 0")
        self.translated_label = QLabel("Translated: 0")
        self.uploaded_label = QLabel("Uploaded: 0")
        self.notion_updated_label = QLabel("Notion Updated: 0")
        self.failed_label = QLabel("Failed (404): 0")
        
        stats_labels = [
            self.total_products_label,
            self.scraped_label,
            self.translated_label,
            self.uploaded_label,
            self.notion_updated_label,
            self.failed_label
        ]
        
        for label in stats_labels:
            label.setFont(QFont("Segoe UI", 9))
            layout.addWidget(label)
    
    def apply_styling(self):
        """Apply styling to stats widget"""
        self.setStyleSheet("""
            QFrame {
                background-color: #44475a;
                border-radius: 8px;
                color: #f8f8f2;
            }
            QLabel {
                color: #f8f8f2;
                padding: 2px 0px;
            }
        """)
    
    def update_stats(self, stats_dict):
        """Update statistics display"""
        self.total_products_label.setText(f"Total Products: {stats_dict.get('total', 0)}")
        self.scraped_label.setText(f"Scraped: {stats_dict.get('scraped', 0)}")
        self.translated_label.setText(f"Translated: {stats_dict.get('translated', 0)}")
        self.uploaded_label.setText(f"Uploaded: {stats_dict.get('uploaded', 0)}")
        self.notion_updated_label.setText(f"Notion Updated: {stats_dict.get('notion_updated', 0)}")
        self.failed_label.setText(f"Failed (404): {stats_dict.get('failed', 0)}")