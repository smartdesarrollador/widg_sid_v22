"""
Quick Access Panel - Small floating window with quick access buttons

Shows buttons for:
- Statistics (📊)
- Tables Manager (📋)
- Favorites (⭐)
- Dashboard (📊)
- Browser (🌐)
- Category Filter (📂)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class QuickAccessPanel(QWidget):
    """Small floating panel with quick access buttons"""

    # Signals for each action
    stats_clicked = pyqtSignal()
    tables_manager_clicked = pyqtSignal()
    favorites_clicked = pyqtSignal()
    dashboard_clicked = pyqtSignal()
    browser_clicked = pyqtSignal()
    category_filter_clicked = pyqtSignal()
    table_creator_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Window properties
        self.setWindowTitle("Acceso Rápido")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        # Fixed size for small panel
        self.setFixedSize(220, 280)

        # Window opacity
        self.setWindowOpacity(0.95)

        # Don't close app when closing this window
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        # Styling
        self.setStyleSheet("""
            QuickAccessPanel {
                background-color: #1e1e1e;
                border: 2px solid #00ff88;
                border-radius: 8px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Header
        header = QLabel("⚡ Acceso Rápido")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11pt;
                font-weight: bold;
                background-color: transparent;
                padding: 5px;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Grid layout for buttons (2 columns)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Create buttons
        buttons_config = [
            ("📊", "Crear Tabla", self.on_table_creator_clicked, 0, 0),
            ("📋", "Tablas", self.on_tables_manager_clicked, 0, 1),
            ("⭐", "Favoritos", self.on_favorites_clicked, 1, 0),
            ("📊", "Estadísticas", self.on_stats_clicked, 1, 1),
            ("🌐", "Navegador", self.on_browser_clicked, 2, 0),
            ("📂", "Filtros", self.on_category_filter_clicked, 2, 1),
            ("📈", "Dashboard", self.on_dashboard_clicked, 3, 0),
        ]

        for icon, tooltip, handler, row, col in buttons_config:
            button = self.create_action_button(icon, tooltip, handler)
            grid_layout.addWidget(button, row, col)

        main_layout.addLayout(grid_layout)

        # Close button
        close_btn = QPushButton("✕ Cerrar")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4475b;
                border-color: #e4475b;
            }
        """)
        close_btn.clicked.connect(self.hide)
        main_layout.addWidget(close_btn)

    def create_action_button(self, icon: str, tooltip: str, handler):
        """Create a styled action button"""
        button = QPushButton(icon)
        button.setFixedSize(95, 50)
        button.setToolTip(tooltip)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                font-size: 20pt;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88,
                    stop:1 #00ccff
                );
                border-color: #00ff88;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
        """)
        button.clicked.connect(handler)
        return button

    # Handlers
    def on_table_creator_clicked(self):
        """Handle table creator button click"""
        self.table_creator_clicked.emit()
        self.hide()

    def on_tables_manager_clicked(self):
        """Handle tables manager button click"""
        self.tables_manager_clicked.emit()
        self.hide()

    def on_favorites_clicked(self):
        """Handle favorites button click"""
        self.favorites_clicked.emit()
        self.hide()

    def on_stats_clicked(self):
        """Handle stats button click"""
        self.stats_clicked.emit()
        self.hide()

    def on_browser_clicked(self):
        """Handle browser button click"""
        self.browser_clicked.emit()
        self.hide()

    def on_category_filter_clicked(self):
        """Handle category filter button click"""
        self.category_filter_clicked.emit()
        self.hide()

    def on_dashboard_clicked(self):
        """Handle dashboard button click"""
        self.dashboard_clicked.emit()
        self.hide()

    def position_near_button(self, button_widget):
        """Position panel near the quick access button"""
        if not button_widget:
            return

        # Get button global position
        button_pos = button_widget.mapToGlobal(button_widget.rect().topLeft())

        # Position to the left of the button
        panel_x = button_pos.x() - self.width() - 10
        panel_y = button_pos.y()

        self.move(panel_x, panel_y)
