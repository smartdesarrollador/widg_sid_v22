"""
ProcessStepWidget - Widget para visualizar y editar un step en el constructor de procesos

Muestra:
- Orden del step
- Label del item
- Tipo de item
- Botones de accion (editar, eliminar, mover)
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.process import ProcessStep


class ProcessStepWidget(QWidget):
    """Widget para un step individual en el constructor de procesos"""

    # Signals
    step_edited = pyqtSignal(object)  # ProcessStep
    step_deleted = pyqtSignal(object)  # ProcessStep
    step_moved_up = pyqtSignal(object)  # ProcessStep
    step_moved_down = pyqtSignal(object)  # ProcessStep

    def __init__(self, step: ProcessStep, is_first: bool = False, is_last: bool = False, parent=None):
        """
        Initialize ProcessStepWidget

        Args:
            step: ProcessStep object
            is_first: Whether this is the first step
            is_last: Whether this is the last step
            parent: Parent widget
        """
        super().__init__(parent)
        self.step = step
        self.is_first = is_first
        self.is_last = is_last
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Container frame for better visual separation
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
            }
            QFrame:hover {
                background-color: #3d3d3d;
                border-color: #007acc;
            }
        """)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(10)

        # Order number
        self.order_label = QLabel(f"{self.step.step_order}.")
        self.order_label.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 14pt;
                font-weight: bold;
                min-width: 30px;
            }
        """)
        container_layout.addWidget(self.order_label)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(3)

        # Step label
        label_text = self.step.get_display_label()
        self.label_widget = QLabel(label_text)
        self.label_widget.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 10pt;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(self.label_widget)

        # Item info (type + content preview)
        info_text = f"{self.step.item_type}"
        if self.step.item_content:
            preview = self.step.item_content[:40]
            if len(self.step.item_content) > 40:
                preview += "..."
            info_text += f" | {preview}"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 8pt;
            }
        """)
        content_layout.addWidget(self.info_label)

        container_layout.addLayout(content_layout, stretch=1)

        # Badges (optional, confirmation, etc.)
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(5)

        if self.step.is_optional:
            optional_badge = QLabel("OPCIONAL")
            optional_badge.setStyleSheet("""
                QLabel {
                    background-color: #ff6b00;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(optional_badge)

        if self.step.wait_for_confirmation:
            confirm_badge = QLabel("ESPERAR")
            confirm_badge.setStyleSheet("""
                QLabel {
                    background-color: #ffa500;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(confirm_badge)

        if not self.step.is_enabled:
            disabled_badge = QLabel("DESHABILITADO")
            disabled_badge.setStyleSheet("""
                QLabel {
                    background-color: #888888;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                    font-weight: bold;
                }
            """)
            badges_layout.addWidget(disabled_badge)

        container_layout.addLayout(badges_layout)

        # Action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(3)

        # Move up button
        self.up_button = QPushButton("↑")
        self.up_button.setFixedSize(24, 24)
        self.up_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.up_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #007acc;
                border-color: #007acc;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555555;
                border-color: #333333;
            }
        """)
        self.up_button.setEnabled(not self.is_first)
        self.up_button.setToolTip("Mover arriba")
        self.up_button.clicked.connect(self.on_move_up)
        buttons_layout.addWidget(self.up_button)

        # Move down button
        self.down_button = QPushButton("↓")
        self.down_button.setFixedSize(24, 24)
        self.down_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.down_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #007acc;
                border-color: #007acc;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555555;
                border-color: #333333;
            }
        """)
        self.down_button.setEnabled(not self.is_last)
        self.down_button.setToolTip("Mover abajo")
        self.down_button.clicked.connect(self.on_move_down)
        buttons_layout.addWidget(self.down_button)

        container_layout.addLayout(buttons_layout)

        # Edit and Delete buttons
        action_buttons_layout = QVBoxLayout()
        action_buttons_layout.setSpacing(3)

        # Edit button
        edit_button = QPushButton("✏")
        edit_button.setFixedSize(24, 24)
        edit_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #00ff88;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #000000;
                border-color: #00ff88;
            }
        """)
        edit_button.setToolTip("Editar configuracion")
        edit_button.clicked.connect(self.on_edit)
        action_buttons_layout.addWidget(edit_button)

        # Delete button
        delete_button = QPushButton("✕")
        delete_button.setFixedSize(24, 24)
        delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #e4475b;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e4475b;
                color: #ffffff;
                border-color: #e4475b;
            }
        """)
        delete_button.setToolTip("Eliminar step")
        delete_button.clicked.connect(self.on_delete)
        action_buttons_layout.addWidget(delete_button)

        container_layout.addLayout(action_buttons_layout)

        main_layout.addWidget(container)

    def update_order(self, new_order: int, is_first: bool, is_last: bool):
        """
        Update step order and button states

        Args:
            new_order: New order number
            is_first: Whether this is now the first step
            is_last: Whether this is now the last step
        """
        self.step.step_order = new_order
        self.is_first = is_first
        self.is_last = is_last

        # Update label
        self.order_label.setText(f"{new_order}.")

        # Update button states
        self.up_button.setEnabled(not is_first)
        self.down_button.setEnabled(not is_last)

    def on_edit(self):
        """Handle edit button click"""
        self.step_edited.emit(self.step)

    def on_delete(self):
        """Handle delete button click"""
        self.step_deleted.emit(self.step)

    def on_move_up(self):
        """Handle move up button click"""
        if not self.is_first:
            self.step_moved_up.emit(self.step)

    def on_move_down(self):
        """Handle move down button click"""
        if not self.is_last:
            self.step_moved_down.emit(self.step)

    def get_step(self) -> ProcessStep:
        """Get the ProcessStep object"""
        return self.step

    def update_step_data(self, step: ProcessStep):
        """
        Update widget with new step data

        Args:
            step: Updated ProcessStep object
        """
        self.step = step

        # Update labels
        self.label_widget.setText(step.get_display_label())

        info_text = f"{step.item_type}"
        if step.item_content:
            preview = step.item_content[:40]
            if len(step.item_content) > 40:
                preview += "..."
            info_text += f" | {preview}"
        self.info_label.setText(info_text)

        # Rebuild the entire widget to reflect changes in badges
        # This is simpler than trying to update badges dynamically
        # Store current state
        current_order = self.step.step_order
        current_is_first = self.is_first
        current_is_last = self.is_last

        # Clear layout
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Reinitialize UI with updated data
        self.init_ui()

        # Restore order state
        self.update_order(current_order, current_is_first, current_is_last)
