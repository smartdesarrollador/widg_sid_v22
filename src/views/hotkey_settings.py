"""
Hotkey Settings
Widget for configuring keyboard shortcuts
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class HotkeySettings(QWidget):
    """
    Hotkey settings widget
    Display and configure keyboard shortcuts
    """

    # Signal emitted when settings change
    settings_changed = pyqtSignal()

    def __init__(self, config_manager=None, parent=None):
        """
        Initialize hotkey settings

        Args:
            config_manager: ConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager

        self.init_ui()
        self.load_hotkeys()

    def init_ui(self):
        """Initialize the UI"""
        # Set background color
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel("Atajos de Teclado")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Configure los atajos de teclado globales. "
            "Los cambios requieren reiniciar la aplicación."
        )
        desc_label.setStyleSheet("color: #999999; font-size: 10pt;")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        # Hotkeys table
        self.hotkeys_table = QTableWidget()
        self.hotkeys_table.setColumnCount(3)
        self.hotkeys_table.setHorizontalHeaderLabels(["Acción", "Combinación", ""])
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.hotkeys_table.horizontalHeader().setDefaultSectionSize(100)
        self.hotkeys_table.verticalHeader().setVisible(False)
        self.hotkeys_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hotkeys_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.hotkeys_table.setMinimumHeight(200)

        # Table styling
        self.hotkeys_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #cccccc;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
                border-right: 1px solid #3d3d3d;
                font-weight: bold;
            }
        """)

        main_layout.addWidget(self.hotkeys_table)

        # Note
        note_label = QLabel(
            "⚠ Los atajos globales funcionan incluso cuando la aplicación está minimizada.\n"
            "Cambiar los atajos requiere reiniciar la aplicación para tomar efecto."
        )
        note_label.setStyleSheet(
            "color: #666666; font-size: 9pt; font-style: italic; "
            "background-color: #252525; padding: 10px; border-radius: 4px;"
        )
        note_label.setWordWrap(True)
        main_layout.addWidget(note_label)

        # Spacer
        main_layout.addStretch()

    def load_hotkeys(self):
        """Load hotkeys into table"""
        # Define default hotkeys
        hotkeys = [
            {
                "action": "Toggle ventana",
                "hotkey": "Ctrl+Shift+V",
                "description": "Mostrar/ocultar ventana del widget"
            },
            {
                "action": "Categoría 1",
                "hotkey": "Ctrl+Shift+1",
                "description": "Abrir primera categoría (próximamente)"
            },
            {
                "action": "Categoría 2",
                "hotkey": "Ctrl+Shift+2",
                "description": "Abrir segunda categoría (próximamente)"
            },
            {
                "action": "Categoría 3",
                "hotkey": "Ctrl+Shift+3",
                "description": "Abrir tercera categoría (próximamente)"
            }
        ]

        # Load from config if available
        if self.config_manager:
            saved_hotkey = self.config_manager.get_setting("hotkey", "ctrl+shift+v")
            # Update first hotkey
            hotkeys[0]["hotkey"] = self.format_hotkey(saved_hotkey)

        # Populate table
        self.hotkeys_table.setRowCount(len(hotkeys))

        for i, hotkey_data in enumerate(hotkeys):
            # Action column
            action_item = QTableWidgetItem(hotkey_data["action"])
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.hotkeys_table.setItem(i, 0, action_item)

            # Hotkey column
            hotkey_item = QTableWidgetItem(hotkey_data["hotkey"])
            hotkey_item.setFlags(hotkey_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            hotkey_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.hotkeys_table.setItem(i, 1, hotkey_item)

            # Change button column
            change_button = QPushButton("Cambiar")
            change_button.setEnabled(i == 0)  # Only enable first one for now
            change_button.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #cccccc;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:hover:enabled {
                    background-color: #3d3d3d;
                    border: 1px solid #007acc;
                }
                QPushButton:disabled {
                    background-color: #252525;
                    color: #555555;
                }
            """)
            change_button.clicked.connect(lambda checked, row=i: self.change_hotkey(row))
            self.hotkeys_table.setCellWidget(i, 2, change_button)

    def format_hotkey(self, hotkey: str) -> str:
        """
        Format hotkey string to display format

        Args:
            hotkey: Hotkey string like "ctrl+shift+v"

        Returns:
            Formatted string like "Ctrl+Shift+V"
        """
        parts = hotkey.split("+")
        formatted_parts = []

        for part in parts:
            part = part.strip().lower()
            if part == "ctrl":
                formatted_parts.append("Ctrl")
            elif part == "shift":
                formatted_parts.append("Shift")
            elif part == "alt":
                formatted_parts.append("Alt")
            else:
                formatted_parts.append(part.upper())

        return "+".join(formatted_parts)

    def change_hotkey(self, row: int):
        """
        Change hotkey for a specific action

        Args:
            row: Row index in table
        """
        # TODO: Implement hotkey capture dialog
        # For now, just show a message
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Cambiar Atajo",
            "La función de cambiar atajos estará disponible próximamente.\n\n"
            "Por ahora, los atajos se pueden editar manualmente en config.json"
        )

    def get_settings(self) -> dict:
        """
        Get current hotkey settings

        Returns:
            Dictionary with hotkey settings
        """
        # Get toggle hotkey from table
        hotkey_item = self.hotkeys_table.item(0, 1)
        if hotkey_item:
            hotkey_text = hotkey_item.text()
            # Convert back to lowercase format
            hotkey = hotkey_text.lower().replace(" ", "")
        else:
            hotkey = "ctrl+shift+v"

        return {
            "hotkey": hotkey
        }
