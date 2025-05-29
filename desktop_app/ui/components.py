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
        ("ID", 70),
        ("Product URL", 200),
        ("Title (Chinese)", 180),
        ("Title (English)", 180),
        ("Scraped", 80),
        ("Translated", 100),
        ("Upl to GD", 100),
        ("Upd on N", 120),
        ("Created", 100)
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


    def setup_table(self):
        """Initialize table structure - GUARANTEED DESCENDING SORT (1000→999→...→1→0)"""
        # Set column count and headers
        self.setColumnCount(len(self.COLUMNS))
        headers = [col[0] for col in self.COLUMNS]
        self.setHorizontalHeaderLabels(headers)

        # Context menu setup
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths
        for i, (header, width) in enumerate(self.COLUMNS):
            self.setColumnWidth(i, width)
        
        # Table behavior settings
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # MUHIM: Sorting BUTUNLAY O'CHIRILGAN - faqat manual control
        self.setSortingEnabled(False)
        
        # Header configuration
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # URL column stretches
        header.setHighlightSections(False)  # Hover effect disabled
        
        # Header click events o'chirish (XAVFSIZ usul)
        try:
            # Agar signal mavjud bo'lsa, custom handler o'rnatish
            header.sectionClicked.connect(self._ignore_header_click)
        except:
            # Agar xato bo'lsa, e'tibor bermaslik
            pass
        
        # Vertical header configuration
        v_header = self.verticalHeader()
        v_header.setVisible(False)  # Hide row numbers for cleaner look
        
        # Grid and visual settings
        self.setShowGrid(True)
        self.setCornerButtonEnabled(False)
        
        # Performance optimizations
        self.setUpdatesEnabled(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def show_context_menu(self, position):
        """Show context menu for table items - optimized version"""
        item = self.itemAt(position)
        if item is None or item.column() != 1:  # Only for URL column
            return
        
        url_text = item.text()
        if not url_text:
            return
        
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
                padding: 12px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #bd93f9;
                color: #282a36;
            }
        """)
        
        copy_action = menu.addAction("📋 Copy URL")
        copy_action.triggered.connect(lambda: self.copy_url_text(url_text))
        
        menu.exec(self.mapToGlobal(position))

    
    # CSS styling ni ham yangilang:
    def apply_styling(self):
        """Apply Dracula theme styling"""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #282a36;
                color: #f8f8f2;
                gridline-color: #44475a;
                border: 1px solid #44475a;
                border-radius: 6px;
                selection-background-color: #bd93f9;
                selection-color: #282a36;
                font-size: 9pt;
                outline: none;
            }
            
            /* Vertical header ni butunlay yashirish */
            QHeaderView::section:vertical {
                width: 0px;
                border: none;
                background: transparent;
            }
            
            QHeaderView::section {
                background-color: #44475a;
                color: #f8f8f2;
                padding: 6px 6px;
                margin: 0px;
                border: none;
                border-right: 1px solid #6272a4;
                border-bottom: 1px solid #6272a4;
                font-weight: bold;
                font-size: 9pt;
                text-align: center;
                min-height: 32px;
            }
            
            /* ID column header */
            QHeaderView::section:first {
                min-width: 60px;
                max-width: 72px;
                text-align: center;
                padding: 8px 4px;
            }
            
            QHeaderView::section:hover {
                background-color: #6272a4;
            }
            
            QTableWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #44475a;
                border-right: 1px solid #44475a;
                text-align: center;
                min-height: 32px;
            }
            
            QTableWidget::item:selected {
                background-color: #bd93f9;
                color: #282a36;
            }
            
            QTableWidget::item:alternate {
                background-color: rgba(68, 71, 90, 0.3);
            }
            
            /* Focus border ni olib tashlash */
            QTableWidget:focus {
                border: 1px solid #44475a;
            }
        """)


    def update_data(self, products_data):
        """Update table with new product data - EXACT DESCENDING ORDER (121→120→119...)"""
        if not products_data:
            self.setRowCount(0)
            return
        
        # Disable updates during batch operation for performance
        self.setUpdatesEnabled(False)
        self.setSortingEnabled(False)  # Disable sorting during update
        
        try:
            # MUHIM: Aynan 121, 120, 119, 118... tartibda saralash
            sorted_products = self._sort_products_descending(products_data)
            
            # Set row count
            self.setRowCount(len(sorted_products))
            
            # Batch insert all data in exact order
            self._populate_table_data(sorted_products)
            
            # Enable sorting AFTER data is populated
            self.setSortingEnabled(True)
            
            # FORCE descending sort by ID (121→120→119→118...)
            self.sortItems(0, Qt.SortOrder.DescendingOrder)
            
        finally:
            # Always re-enable updates
            self.setUpdatesEnabled(True)
            self.update()  # Force refresh
            
    
    def _sort_products_descending(self, products_data):
        """ANIQ DESCENDING TARTIB: 121→120→119→118→...→99→98→97"""
        try:
            def get_numeric_id(product):
                """Extract numeric ID for sorting"""
                if isinstance(product, (tuple, list)):
                    product_id = product[0]
                else:
                    product_id = product.get('id', 0)
                
                # Convert to integer, handle various formats
                if product_id is None:
                    return 0
                
                try:
                    return int(product_id)
                except (ValueError, TypeError):
                    return 0
            
            # MUHIM: reverse=True -> DESCENDING order (121, 120, 119, 118...)
            sorted_data = sorted(products_data, key=get_numeric_id, reverse=True)
            
            # Debug: birinchi 5 ta ID ni ko'rsatish
            if sorted_data:
                first_5_ids = [get_numeric_id(p) for p in sorted_data[:5]]
                print(f"Saralangan ID lar (birinchi 5 ta): {first_5_ids}")
            
            return sorted_data
            
        except Exception as e:
            print(f"Saralash xatosi: {e}")
            return products_data
    
    def _populate_table_data(self, sorted_products):
        """Efficiently populate table with sorted data"""
        for row, product in enumerate(sorted_products):
            try:
                # Extract data from product tuple/dict
                if isinstance(product, (tuple, list)):
                    product_id, url, title_chn, title_en, scraped, translated, uploaded, notion, created = product
                else:
                    # Handle dict format
                    product_id = product.get('id', 0)
                    url = product.get('product_url', '')
                    title_chn = product.get('title_chn', '')
                    title_en = product.get('title_en', '')
                    scraped = product.get('scraped_status', 0)
                    translated = product.get('translated_status', 0)
                    uploaded = product.get('uploaded_to_gd_status', 0)
                    notion = product.get('updated_on_notion_status', 0)
                    created = product.get('created_at', '')
                
                # Create and set items efficiently
                self.setItem(row, 0, self.create_id_cell(product_id))
                self.setItem(row, 1, self.create_url_cell(url))
                self.setItem(row, 2, self.create_cell_item(title_chn or ""))
                self.setItem(row, 3, self.create_cell_item(title_en or ""))
                self.setItem(row, 4, self.create_status_cell(scraped))
                self.setItem(row, 5, self.create_status_cell(translated))
                self.setItem(row, 6, self.create_status_cell(uploaded))
                self.setItem(row, 7, self.create_status_cell(notion))
                self.setItem(row, 8, self.create_cell_item(self.format_datetime(created)))
                
            except Exception as e:
                print(f"Error populating row {row}: {e}")
                continue


    def create_id_cell(self, product_id):
        """INT SORTING uchun to'g'rilangan ID cell"""
        # Integer ga aylantirish
        try:
            numeric_id = int(product_id) if product_id is not None else 0
        except (ValueError, TypeError):
            numeric_id = 0
        
        # Display text
        display_text = str(numeric_id)
        
        # QTableWidgetItem yaratish
        item = QTableWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # MUHIM: INT SORTING uchun numeric data o'rnatish
        item.setData(Qt.ItemDataRole.DisplayRole, numeric_id)  # INT qiymat!
        item.setData(Qt.ItemDataRole.UserRole, numeric_id)     # Backup INT
        
        # ID cell styling
        item.setBackground(QColor("#6272a4"))
        item.setForeground(QColor("#f8f8f2"))
        
        return item

    def create_cell_item(self, text, data_type="text"):
        """Create a standard table cell item - OPTIMIZED"""
        display_text = str(text) if text is not None else ""
        item = QTableWidgetItem(display_text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Set appropriate data for sorting
        if data_type == "number":
            try:
                numeric_val = int(text) if text else 0
                item.setData(Qt.ItemDataRole.UserRole, numeric_val)
            except (ValueError, TypeError):
                item.setData(Qt.ItemDataRole.UserRole, 0)
        else:
            # Text data uchun ham UserRole o'rnatamiz
            item.setData(Qt.ItemDataRole.UserRole, display_text)
        
        return item

    def create_url_cell(self, url):
        """Create URL cell with special formatting - OPTIMIZED"""
        url_text = str(url) if url else ""
        item = self.create_cell_item(url_text)
        
        # Highlight problematic URLs
        if "404" in url_text or not url_text.strip():
            item.setBackground(QColor("#ff5555"))
            item.setForeground(QColor("#ffffff"))
        elif url_text.startswith("http"):
            # Valid URL styling
            item.setForeground(QColor("#8be9fd"))
        
        return item
    
    def create_status_cell(self, status):
        """Create status cell with colored indicators - OPTIMIZED"""
        # Use boolean check for consistency
        is_completed = bool(status)
        status_text = "✅" if is_completed else "⚪"
        
        item = QTableWidgetItem(status_text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Set sorting data
        item.setData(Qt.ItemDataRole.UserRole, 1 if is_completed else 0)
        
        # Color coding with better contrast
        if is_completed:
            item.setBackground(QColor("#50fa7b"))  # Green for completed
            item.setForeground(QColor("#282a36"))
        else:
            item.setBackground(QColor("#ffb86c"))  # Orange for pending
            item.setForeground(QColor("#282a36"))
        
        return item
    
    def format_datetime(self, dt_str):
        """Format datetime string for display - OPTIMIZED"""
        if not dt_str:
            return ""
        
        try:
            # Handle different datetime formats
            if isinstance(dt_str, str):
                # Remove 'Z' and handle timezone
                clean_dt = dt_str.replace('Z', '+00:00')
                dt = datetime.fromisoformat(clean_dt)
            else:
                dt = dt_str
            
            # Format as MM/DD HH:MM
            return dt.strftime("%m/%d %H:%M")
        except Exception as e:
            # Fallback: return first 16 characters
            return str(dt_str)[:16]

    def apply_styling(self):
        """Apply Dracula theme styling - OPTIMIZED"""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #282a36;
                color: #f8f8f2;
                gridline-color: #44475a;
                border: 1px solid #44475a;
                border-radius: 6px;
                selection-background-color: #bd93f9;
                selection-color: #282a36;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 9pt;
                outline: none;
            }
            
            /* Header styling */
            QHeaderView::section {
                background-color: #44475a;
                color: #f8f8f2;
                padding: 8px 6px;
                margin: 0px;
                border: none;
                border-right: 1px solid #6272a4;
                border-bottom: 1px solid #6272a4;
                font-weight: bold;
                font-size: 9pt;
                text-align: center;
                min-height: 28px;
            }
            
            /* ID column header special styling */
            QHeaderView::section:first {
                background-color: #6272a4;
                color: #f8f8f2;
                font-weight: bold;
                min-width: 60px;
                max-width: 80px;
            }
            
            QHeaderView::section:hover {
                background-color: #6272a4;
                color: #f8f8f2;
            }
            
            /* Table cells */
            QTableWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #44475a;
                border-right: 1px solid #44475a;
                min-height: 28px;
                text-align: center;
            }
            
            QTableWidget::item:selected {
                background-color: #bd93f9;
                color: #282a36;
                font-weight: bold;
            }
            
            QTableWidget::item:alternate {
                background-color: rgba(68, 71, 90, 0.2);
            }
            
            /* Focus styling */
            QTableWidget:focus {
                border: 2px solid #bd93f9;
            }
            
            /* Scrollbar styling */
            QScrollBar:vertical {
                background-color: #44475a;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #6272a4;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #bd93f9;
            }
        """)

    # Additional utility methods
    def refresh_data(self, products_data):
        """Ma'lumotlarni yangilash - ANIQ DESCENDING ORDER bilan"""
        print("🔄 Ma'lumotlar yangilanmoqda...")
        self.update_data(products_data)
        self.verify_sort_order()
    
    def verify_sort_order(self):
        """Saralash tartibini tekshirish"""
        if self.rowCount() == 0:
            print("📋 Jadval bo'sh")
            return
        
        print(f"📊 Jadval holati:")
        print(f"   - Jami qatorlar: {self.rowCount()}")
        
        # Birinchi va oxirgi ID larni olish
        if self.rowCount() > 0:
            first_item = self.item(0, 0)
            last_item = self.item(self.rowCount()-1, 0)
            
            if first_item and last_item:
                first_id = first_item.text()
                last_id = last_item.text()
                
                print(f"   - Birinchi ID: {first_id}")
                print(f"   - Oxirgi ID: {last_id}")
                
                # Tartib tekshiruvi
                try:
                    first_num = int(first_id)
                    last_num = int(last_id)
                    
                    if first_num > last_num:
                        print("   ✅ Tartib: DESCENDING (to'g'ri)")
                    else:
                        print("   ❌ Tartib: ASCENDING (noto'g'ri)")
                        print("   🔧 Manual tuzatish kerak!")
                        
                except:
                    print("   ⚠️ ID larni tekshirib bo'lmadi")
        
        # Birinchi 10 ta ID ni ko'rsatish
        if self.rowCount() >= 10:
            first_10_ids = []
            for i in range(10):
                item = self.item(i, 0)
                if item:
                    first_10_ids.append(item.text())
            
            print(f"   📝 Birinchi 10 ta ID: {' → '.join(first_10_ids)}")
    
    def manual_descending_fix(self):
        """Agar saralash noto'g'ri bo'lsa, manual tuzatish"""
        print("🔧 Manual DESCENDING saralash...")
        
        # Barcha ma'lumotlarni olish
        all_data = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            all_data.append(row_data)
        
        # ID bo'yicha saralash
        try:
            all_data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=False)
            
            # Qayta joylash
            self.setUpdatesEnabled(False)
            for row, row_data in enumerate(all_data):
                for col, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(cell_data)
                    if col == 0:  # ID column
                        item.setBackground(QColor("#6272a4"))
                        item.setForeground(QColor("#f8f8f2"))
                    self.setItem(row, col, item)
            
            self.setUpdatesEnabled(True)
            print("✅ Manual saralash tugadi!")
            
        except Exception as e:
            print(f"❌ Manual saralash xatosi: {e}")
    
    def get_selected_product_id(self):
        """Tanlangan mahsulot ID sini olish"""
        current_row = self.currentRow()
        if current_row >= 0:
            id_item = self.item(current_row, 0)
            if id_item:
                return id_item.text()
        return None
    
    def clear_table(self):
        """Jadvalni tozalash"""
        self.setUpdatesEnabled(False)
        self.clearContents()
        self.setRowCount(0)
        self.setUpdatesEnabled(True)
        print("🗑️ Jadval tozalandi")

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