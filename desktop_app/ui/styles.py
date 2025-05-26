"""
PyDracula Theme Styles for the Desktop Application
Professional dark theme with modern styling
"""


class DraculaTheme:
    """Dracula color scheme and styling constants"""
    
    # Color palette
    COLORS = {
        'background': '#282a36',
        'current_line': '#44475a',
        'foreground': '#f8f8f2',
        'comment': '#6272a4',
        'cyan': '#8be9fd',
        'green': '#50fa7b',
        'orange': '#ffb86c',
        'pink': '#ff79c6',
        'purple': '#bd93f9',
        'red': '#ff5555',
        'yellow': '#f1fa8c'
    }
    
    @classmethod
    def get_main_style(cls):
        """Main application styling"""
        return f"""
            QMainWindow {{
                background-color: {cls.COLORS['background']};
                color: {cls.COLORS['foreground']};
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            
            QWidget {{
                background-color: {cls.COLORS['background']};
                color: {cls.COLORS['foreground']};
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {cls.COLORS['current_line']};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {cls.COLORS['comment']};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {cls.COLORS['purple']};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {cls.COLORS['current_line']};
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {cls.COLORS['comment']};
                border-radius: 6px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {cls.COLORS['purple']};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
    
    @classmethod
    def get_header_style(cls):
        """Header section styling"""
        return f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {cls.COLORS['background']}, 
                    stop:1 {cls.COLORS['current_line']}
                );
                border-bottom: 2px solid {cls.COLORS['purple']};
            }}
        """
    
    @classmethod
    def get_title_style(cls):
        """Title label styling"""
        return f"""
            QLabel {{
                color: {cls.COLORS['purple']};
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }}
        """
    
    @classmethod
    def get_panel_style(cls):
        """Panel frame styling"""
        return f"""
            QFrame {{
                background-color: {cls.COLORS['background']};
                border: 1px solid {cls.COLORS['current_line']};
                border-radius: 8px;
                margin: 5px;
            }}
        """
    
    @classmethod
    def get_panel_header_style(cls):
        """Panel header styling"""
        return f"""
            QLabel {{
                color: {cls.COLORS['cyan']};
                background-color: transparent;
                padding: 8px;
                border-bottom: 1px solid {cls.COLORS['current_line']};
                margin-bottom: 5px;
            }}
        """
    
    @classmethod
    def get_table_style(cls):
        """Table widget styling"""
        return f"""
            QTableWidget {{
                background-color: {cls.COLORS['background']};
                color: {cls.COLORS['foreground']};
                gridline-color: {cls.COLORS['current_line']};
                border: 1px solid {cls.COLORS['current_line']};
                border-radius: 6px;
                selection-background-color: {cls.COLORS['purple']};
                selection-color: {cls.COLORS['background']};
                font-size: 9pt;
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {cls.COLORS['current_line']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {cls.COLORS['purple']};
                color: {cls.COLORS['background']};
            }}
            
            QTableWidget::item:alternate {{
                background-color: rgba(68, 71, 90, 0.3);
            }}
            
            QHeaderView::section {{
                background-color: {cls.COLORS['current_line']};
                color: {cls.COLORS['foreground']};
                padding: 8px;
                border: none;
                border-right: 1px solid {cls.COLORS['background']};
                font-weight: bold;
                font-size: 9pt;
            }}
            
            QHeaderView::section:hover {{
                background-color: {cls.COLORS['comment']};
            }}
            
            QTableWidget::corner {{
                background-color: {cls.COLORS['current_line']};
            }}
        """
    
    @classmethod
    def get_log_viewer_style(cls):
        """Log viewer styling"""
        return f"""
            QTextEdit {{
                background-color: #1e1f29;
                color: {cls.COLORS['foreground']};
                border: 1px solid {cls.COLORS['current_line']};
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                padding: 8px;
                line-height: 1.4;
            }}
            
            QTextEdit:focus {{
                border: 2px solid {cls.COLORS['purple']};
            }}
        """
    
    @classmethod
    def get_splitter_style(cls):
        """Splitter styling"""
        return f"""
            QSplitter::handle {{
                background-color: {cls.COLORS['current_line']};
                margin: 2px;
            }}
            
            QSplitter::handle:horizontal {{
                width: 3px;
                border-radius: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 3px;
                border-radius: 1px;
            }}
            
            QSplitter::handle:hover {{
                background-color: {cls.COLORS['purple']};
            }}
        """
    
    @classmethod
    def get_status_bar_style(cls):
        """Status bar styling"""
        return f"""
            QStatusBar {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {cls.COLORS['current_line']}, 
                    stop:1 {cls.COLORS['background']}
                );
                color: {cls.COLORS['foreground']};
                border-top: 1px solid {cls.COLORS['comment']};
                padding: 5px;
                font-size: 9pt;
            }}
            
            QStatusBar::item {{
                border: none;
            }}
        """
    
    @classmethod
    def get_button_style(cls, button_type="primary"):
        """Button styling based on type"""
        color_map = {
            'primary': cls.COLORS['purple'],
            'success': cls.COLORS['green'],
            'warning': cls.COLORS['orange'],
            'danger': cls.COLORS['red'],
            'info': cls.COLORS['cyan']
        }
        
        bg_color = color_map.get(button_type, cls.COLORS['purple'])
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {cls.COLORS['background']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 9pt;
            }}
            
            QPushButton:hover {{
                background-color: {cls._lighten_color(bg_color)};
            }}
            
            QPushButton:pressed {{
                background-color: {cls._darken_color(bg_color)};
            }}
            
            QPushButton:disabled {{
                background-color: {cls.COLORS['comment']};
                color: {cls.COLORS['current_line']};
            }}
        """
    
    @classmethod
    def get_dialog_style(cls):
        """Dialog window styling"""
        return f"""
            QWidget {{
                background-color: {cls.COLORS['background']};
                color: {cls.COLORS['foreground']};
            }}
            
            QLabel {{
                color: {cls.COLORS['foreground']};
                font-size: 10pt;
            }}
            
            QCheckBox {{
                color: {cls.COLORS['foreground']};
                spacing: 5px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {cls.COLORS['comment']};
                border-radius: 3px;
                background-color: {cls.COLORS['background']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {cls.COLORS['green']};
                border-color: {cls.COLORS['green']};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNEw2IDExLjMzMzNMMi42NjY2NyA4IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {cls.COLORS['purple']};
            }}
        """
    
    @classmethod
    def get_menu_style(cls):
        """Menu and context menu styling"""
        return f"""
            QMenu {{
                background-color: {cls.COLORS['current_line']};
                color: {cls.COLORS['foreground']};
                border: 1px solid {cls.COLORS['comment']};
                border-radius: 6px;
                padding: 4px;
            }}
            
            QMenu::item {{
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {cls.COLORS['purple']};
                color: {cls.COLORS['background']};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {cls.COLORS['comment']};
                margin: 4px 8px;
            }}
        """
    
    @classmethod
    def get_tooltip_style(cls):
        """Tooltip styling"""
        return f"""
            QToolTip {{
                background-color: {cls.COLORS['current_line']};
                color: {cls.COLORS['foreground']};
                border: 1px solid {cls.COLORS['comment']};
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
            }}
        """
    
    @classmethod
    def get_tab_style(cls):
        """Tab widget styling"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {cls.COLORS['current_line']};
                border-radius: 6px;
                background-color: {cls.COLORS['background']};
            }}
            
            QTabBar::tab {{
                background-color: {cls.COLORS['current_line']};
                color: {cls.COLORS['foreground']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {cls.COLORS['purple']};
                color: {cls.COLORS['background']};
            }}
            
            QTabBar::tab:hover {{
                background-color: {cls.COLORS['comment']};
            }}
        """
    
    @staticmethod
    def _lighten_color(color):
        """Lighten a hex color by 10%"""
        # Simple color lightening (for hover effects)
        color_map = {
            '#bd93f9': '#c9a6fa',
            '#50fa7b': '#5af78e',
            '#ffb86c': '#ffc374',
            '#ff5555': '#ff6b6b',
            '#8be9fd': '#96ebfd'
        }
        return color_map.get(color, color)
    
    @staticmethod
    def _darken_color(color):
        """Darken a hex color by 10%"""
        # Simple color darkening (for pressed effects)
        color_map = {
            '#bd93f9': '#a87ef5',
            '#50fa7b': '#45e56d',
            '#ffb86c': '#f5ad5f',
            '#ff5555': '#f54848',
            '#8be9fd': '#7de4f7'
        }
        return color_map.get(color, color)