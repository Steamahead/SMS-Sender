COLORS = {
    "bg": "#FAFBFC",
    "panel": "#FFFFFF",
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent_light": "#DBEAFE",
    "success": "#16A34A",
    "error": "#DC2626",
    "error_light": "#FEE2E2",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "text_dim": "#9CA3AF",
    "border": "#E5E7EB",
    "input_bg": "#F9FAFB",
    "input_focus": "#2563EB",
}

FONT_FAMILY = "Segoe UI"

QSS = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}

QWidget {{
    font-family: "{FONT_FAMILY}";
    font-size: 13px;
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

QLabel[class="header"] {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['text']};
}}

QLabel[class="section"] {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text']};
}}

QPushButton {{
    background-color: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    color: {COLORS['text']};
}}

QPushButton:hover {{
    background-color: {COLORS['bg']};
    border-color: {COLORS['accent']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_light']};
}}

QPushButton:disabled {{
    color: {COLORS['text_dim']};
    border-color: {COLORS['border']};
    background-color: {COLORS['bg']};
}}

QPushButton[class="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_dark']});
    color: white;
    border: none;
    font-weight: bold;
    padding: 10px 24px;
}}

QPushButton[class="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent_dark']}, stop:1 #1E40AF);
}}

QPushButton[class="primary"]:disabled {{
    background: {COLORS['text_dim']};
}}

QPushButton[class="danger"] {{
    background-color: {COLORS['error']};
    color: white;
    border: none;
    font-weight: bold;
}}

QLineEdit, QComboBox {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus, QComboBox:focus {{
    border-color: {COLORS['input_focus']};
    background-color: white;
}}

QTextEdit {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}}

QTextEdit:focus {{
    border-color: {COLORS['input_focus']};
    background-color: white;
}}

QTableWidget {{
    background-color: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 6px 8px;
}}

QHeaderView::section {{
    background-color: {COLORS['bg']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}

QProgressBar {{
    background-color: {COLORS['border']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_dark']});
    border-radius: 4px;
}}

QTabWidget::pane {{
    border: none;
    background: {COLORS['bg']};
}}

QTabBar::tab {{
    background: transparent;
    border: none;
    padding: 10px 20px;
    font-size: 13px;
    color: {COLORS['text_secondary']};
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom-color: {COLORS['accent']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    color: {COLORS['text']};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['text_dim']};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QGroupBox {{
    background-color: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 8px;
    padding: 16px;
    padding-top: 28px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}
"""
