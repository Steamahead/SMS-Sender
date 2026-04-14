COLORS = {
    "bg": "#F5F6F8",
    "surface": "#FFFFFF",
    "panel": "#FFFFFF",
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent_hover": "#1D4ED8",
    "accent_light": "#DBEAFE",
    "success": "#16A34A",
    "error": "#DC2626",
    "error_light": "#FEE2E2",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "text_dim": "#9CA3AF",
    "border": "#D1D5DB",
    "hover": "#F3F4F6",
    "input_bg": "#F9FAFB",
    "input_focus": "#2563EB",
}

FONT_FAMILY = "Segoe UI"

QSS = f"""
* {{
    font-family: "{FONT_FAMILY}";
}}

QWidget {{
    font-size: 13px;
    color: {COLORS['text']};
    background-color: {COLORS['bg']};
}}

QMainWindow {{
    background-color: {COLORS['bg']};
}}

QTabWidget::pane {{
    background-color: {COLORS['bg']};
    border: none;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 8px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom: 2px solid {COLORS['accent']};
}}

QTabBar::tab:hover {{
    color: {COLORS['text']};
}}

QLabel {{
    color: {COLORS['text']};
    background: transparent;
}}

QLabel[class="dim"] {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}

QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 8px;
    padding: 12px;
    padding-top: 12px;
}}

QGroupBox::title {{
    subcontrol-origin: padding;
    subcontrol-position: top left;
    padding: 0 4px;
    color: {COLORS['text']};
    font-size: 13px;
    font-weight: 600;
    background-color: transparent;
}}

QPushButton {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 5px 14px;
    color: {COLORS['text']};
}}

QPushButton:hover {{
    background-color: {COLORS['hover']};
    border-color: {COLORS['text_secondary']};
}}

QPushButton:pressed {{
    background-color: {COLORS['border']};
}}

QPushButton[class="primary"] {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    padding: 7px 20px;
}}

QPushButton[class="primary"]:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton[class="primary"]:disabled {{
    background: {COLORS['text_dim']};
}}

QPushButton:disabled {{
    background-color: {COLORS['hover']};
    color: {COLORS['text_dim']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[class="danger"] {{
    background-color: {COLORS['error']};
    color: white;
    border: none;
}}

QLineEdit, QTextEdit, QComboBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: {COLORS['accent']};
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border-color: {COLORS['input_focus']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QTableWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    gridline-color: transparent;
    alternate-background-color: {COLORS['hover']};
    selection-background-color: {COLORS['accent_light']};
    selection-color: {COLORS['text']};
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 4px 6px;
}}

QHeaderView::section {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_secondary']};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-weight: 600;
    font-size: 12px;
}}

QProgressBar {{
    border: none;
    border-radius: 3px;
    background-color: {COLORS['border']};
    text-align: center;
    max-height: 6px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 3px;
}}

QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['text_dim']};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QSplitter::handle {{
    background-color: {COLORS['border']};
    height: 2px;
}}
"""
