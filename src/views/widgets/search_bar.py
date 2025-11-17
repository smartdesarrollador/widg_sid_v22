"""
SearchBar Widget for Widget Sidebar
Custom QLineEdit with debouncing and clear button functionality
"""

from PyQt6.QtWidgets import QLineEdit, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont


class SearchBar(QWidget):
    """
    Search bar widget with debouncing
    Emits search_changed signal after 300ms of user inactivity
    """

    search_changed = pyqtSignal(str)  # Emits search query

    def __init__(self, parent=None):
        """Initialize search bar with debouncing"""
        super().__init__(parent)

        # Debounce timer (300ms)
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)  # 300ms delay
        self.debounce_timer.timeout.connect(self._emit_search)

        # Current query
        self.current_query = ""

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

    def _setup_ui(self):
        """Setup UI components"""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar items...")
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setFixedHeight(32)

        # Clear button
        self.clear_button = QPushButton("×")
        self.clear_button.setFixedSize(32, 32)
        self.clear_button.setFont(QFont("Segoe UI", 16))
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.hide()  # Hidden by default

        # Add widgets to layout
        layout.addWidget(self.search_input)
        layout.addWidget(self.clear_button)

    def _connect_signals(self):
        """Connect internal signals"""
        self.search_input.textChanged.connect(self._on_text_changed)
        self.clear_button.clicked.connect(self.clear_search)

    def _apply_styles(self):
        """Apply dark theme styles"""
        # SearchBar container style
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
            }
        """)

        # Search input style
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
                background-color: #333333;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)

        # Clear button style
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-size: 16pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #007acc;
            }
            QPushButton:pressed {
                background-color: #007acc;
                color: #ffffff;
            }
        """)

    def _on_text_changed(self, text: str):
        """
        Handle text change with debouncing

        Args:
            text: New text in search input
        """
        # Show/hide clear button
        if text:
            self.clear_button.show()
        else:
            self.clear_button.hide()

        # Restart debounce timer
        self.debounce_timer.stop()
        self.current_query = text
        self.debounce_timer.start()

    def _emit_search(self):
        """Emit search_changed signal after debounce delay"""
        self.search_changed.emit(self.current_query)

    def clear_search(self):
        """Clear search input and emit empty query"""
        self.search_input.clear()
        self.current_query = ""
        self.clear_button.hide()
        self.search_changed.emit("")

    def get_query(self) -> str:
        """
        Get current search query

        Returns:
            Current query text
        """
        return self.search_input.text()

    def set_query(self, query: str):
        """
        Set search query programmatically

        Args:
            query: Query text to set
        """
        self.search_input.setText(query)

    def set_focus(self):
        """Set focus to search input"""
        self.search_input.setFocus()

    def setPlaceholderText(self, text: str):
        """
        Set placeholder text for search input

        Args:
            text: Placeholder text to display
        """
        self.search_input.setPlaceholderText(text)
