"""
ProcessWidget - Widget para mostrar un proceso en el panel flotante

Características:
- Header con nombre, icono, badges
- Metadata (steps count, uso, fecha)
- Lista de steps (expandible/colapsable)
- Botones de acción (ejecutar, copiar todo, editar, pin, eliminar)
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import sys
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.process import Process

# Get logger
logger = logging.getLogger(__name__)


class ProcessWidget(QWidget):
    """Widget for displaying a process in the floating panel"""

    # Signals
    process_executed = pyqtSignal(int)  # process_id
    process_edited = pyqtSignal(int)
    process_deleted = pyqtSignal(int)
    process_pinned = pyqtSignal(int, bool)  # process_id, is_pinned
    copy_all_requested = pyqtSignal(int)

    def __init__(self, process: Process, parent=None):
        super().__init__(parent)
        self.process = process
        self.is_expanded = False
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container frame
        self.container = QFrame()
        self.container.setFrameShape(QFrame.Shape.StyledPanel)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 0px;
            }
            QFrame:hover {
                background-color: #353535;
                border-color: #ff6b00;
            }
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ========== HEADER ==========
        self.create_header(container_layout)

        # ========== METADATA ==========
        self.create_metadata(container_layout)

        # ========== STEPS LIST (collapsable) ==========
        self.create_steps_list(container_layout)

        # ========== ACTIONS ==========
        self.create_actions(container_layout)

        main_layout.addWidget(self.container)

    def create_header(self, parent_layout):
        """Create header with name, icon, badges"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom: 1px solid #3d3d3d;
                padding: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)

        # Icon
        icon_label = QLabel(self.process.icon or "⚙️")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                background-color: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(icon_label)

        # Name
        name_label = QLabel(self.process.name)
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11pt;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(name_label, stretch=1)

        # Pin badge (if pinned)
        if self.process.is_pinned:
            pin_badge = QLabel("📌")
            pin_badge.setStyleSheet("""
                QLabel {
                    color: #00ff88;
                    font-size: 12pt;
                    background-color: transparent;
                    border: none;
                }
            """)
            pin_badge.setToolTip("Proceso anclado")
            header_layout.addWidget(pin_badge)

        # Expand/collapse button
        self.expand_button = QPushButton("▼")
        self.expand_button.setFixedSize(24, 24)
        self.expand_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.expand_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 12px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #ff6b00;
                border-color: #ff6b00;
            }
        """)
        self.expand_button.setToolTip("Expandir/colapsar steps")
        self.expand_button.clicked.connect(self.toggle_expand)
        header_layout.addWidget(self.expand_button)

        # Quick execute button
        quick_execute_button = QPushButton("⚡")
        quick_execute_button.setFixedSize(24, 24)
        quick_execute_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        quick_execute_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ff6b00;
                border: 1px solid #555555;
                border-radius: 12px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #ff6b00;
                color: #ffffff;
                border-color: #ff6b00;
            }
        """)
        quick_execute_button.setToolTip("Ejecutar proceso")
        quick_execute_button.clicked.connect(self.on_execute_clicked)
        header_layout.addWidget(quick_execute_button)

        parent_layout.addWidget(header_widget)

    def create_metadata(self, parent_layout):
        """Create metadata section"""
        metadata_widget = QWidget()
        metadata_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom: 1px solid #3d3d3d;
                padding: 4px;
            }
        """)
        metadata_layout = QHBoxLayout(metadata_widget)
        metadata_layout.setContentsMargins(12, 4, 12, 4)
        metadata_layout.setSpacing(0)

        # Build metadata text
        steps_count = len(self.process.steps) if self.process.steps else 0
        use_count = self.process.use_count or 0

        # Get relative time
        relative_time = self.get_relative_time(self.process.last_used) if self.process.last_used else "Nunca usado"

        metadata_text = f"{steps_count} step(s) • Usado {use_count} veces • {relative_time}"

        # Description (if exists)
        if self.process.description:
            desc_label = QLabel(self.process.description)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 9pt;
                    background-color: transparent;
                    border: none;
                }
            """)
            desc_label.setWordWrap(True)
            metadata_layout.addWidget(desc_label, stretch=1)
        else:
            # Just metadata
            meta_label = QLabel(metadata_text)
            meta_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 9pt;
                    background-color: transparent;
                    border: none;
                }
            """)
            metadata_layout.addWidget(meta_label, stretch=1)

        parent_layout.addWidget(metadata_widget)

        # If has description, add metadata below
        if self.process.description:
            meta_widget2 = QWidget()
            meta_widget2.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border-bottom: 1px solid #3d3d3d;
                    padding: 0px;
                }
            """)
            meta_layout2 = QHBoxLayout(meta_widget2)
            meta_layout2.setContentsMargins(12, 0, 12, 4)

            meta_label2 = QLabel(metadata_text)
            meta_label2.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 8pt;
                    background-color: transparent;
                    border: none;
                }
            """)
            meta_layout2.addWidget(meta_label2)

            parent_layout.addWidget(meta_widget2)

    def create_steps_list(self, parent_layout):
        """Create collapsable steps list"""
        self.steps_widget = QWidget()
        self.steps_widget.setVisible(False)  # Hidden by default
        self.steps_widget.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-bottom: 1px solid #3d3d3d;
                padding: 0px;
            }
        """)

        steps_layout = QVBoxLayout(self.steps_widget)
        steps_layout.setContentsMargins(12, 8, 12, 8)
        steps_layout.setSpacing(4)

        # Separator
        separator = QLabel("━━━ Steps ━━━")
        separator.setStyleSheet("""
            QLabel {
                color: #555555;
                font-size: 8pt;
                background-color: transparent;
                border: none;
            }
        """)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        steps_layout.addWidget(separator)

        # Steps list
        if self.process.steps:
            for step in self.process.steps:
                step_label_text = step.custom_label or step.item_label

                # Step item
                step_item = QLabel(f"{step.step_order}. {step_label_text}")
                step_item.setStyleSheet("""
                    QLabel {
                        color: #cccccc;
                        font-size: 9pt;
                        background-color: transparent;
                        border: none;
                        padding: 2px;
                    }
                """)
                steps_layout.addWidget(step_item)
        else:
            no_steps_label = QLabel("Sin steps")
            no_steps_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 9pt;
                    font-style: italic;
                    background-color: transparent;
                    border: none;
                }
            """)
            steps_layout.addWidget(no_steps_label)

        parent_layout.addWidget(self.steps_widget)

    def create_actions(self, parent_layout):
        """Create action buttons"""
        actions_widget = QWidget()
        actions_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                padding: 8px;
            }
        """)
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(12, 8, 12, 8)
        actions_layout.setSpacing(8)

        # Execute button
        execute_button = QPushButton("⚡ Ejecutar")
        execute_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        execute_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ff6b00;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b00;
                color: #ffffff;
                border-color: #ff6b00;
            }
        """)
        execute_button.clicked.connect(self.on_execute_clicked)
        actions_layout.addWidget(execute_button)

        # Copy all button
        copy_all_button = QPushButton("📋 Copiar")
        copy_all_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_all_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #00ff88;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #000000;
                border-color: #00ff88;
            }
        """)
        copy_all_button.setToolTip("Copiar todos los steps al portapapeles")
        copy_all_button.clicked.connect(self.on_copy_all_clicked)
        actions_layout.addWidget(copy_all_button)

        # Edit button
        edit_button = QPushButton("✏️")
        edit_button.setFixedSize(28, 28)
        edit_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #00ccff;
                border: 1px solid #555555;
                border-radius: 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #00ccff;
                color: #000000;
                border-color: #00ccff;
            }
        """)
        edit_button.setToolTip("Editar proceso")
        edit_button.clicked.connect(self.on_edit_clicked)
        actions_layout.addWidget(edit_button)

        # Pin button
        pin_text = "📌" if self.process.is_pinned else "📍"
        self.pin_button = QPushButton(pin_text)
        self.pin_button.setFixedSize(28, 28)
        self.pin_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pin_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #00ff88;
                border: 1px solid #555555;
                border-radius: 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #000000;
                border-color: #00ff88;
            }
        """)
        self.pin_button.setToolTip("Anclar/desanclar proceso")
        self.pin_button.clicked.connect(self.on_pin_clicked)
        actions_layout.addWidget(self.pin_button)

        # Delete button
        delete_button = QPushButton("❌")
        delete_button.setFixedSize(28, 28)
        delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #e4475b;
                border: 1px solid #555555;
                border-radius: 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e4475b;
                color: #ffffff;
                border-color: #e4475b;
            }
        """)
        delete_button.setToolTip("Eliminar proceso")
        delete_button.clicked.connect(self.on_delete_clicked)
        actions_layout.addWidget(delete_button)

        parent_layout.addWidget(actions_widget)

    # ========== ACTIONS ==========

    def toggle_expand(self):
        """Toggle steps list visibility"""
        self.is_expanded = not self.is_expanded
        self.steps_widget.setVisible(self.is_expanded)

        # Update button
        if self.is_expanded:
            self.expand_button.setText("▲")
        else:
            self.expand_button.setText("▼")

    def on_execute_clicked(self):
        """Handle execute button click"""
        self.process_executed.emit(self.process.id)

    def on_copy_all_clicked(self):
        """Handle copy all button click"""
        self.copy_all_requested.emit(self.process.id)

    def on_edit_clicked(self):
        """Handle edit button click"""
        self.process_edited.emit(self.process.id)

    def on_pin_clicked(self):
        """Handle pin button click"""
        new_state = not self.process.is_pinned
        self.process_pinned.emit(self.process.id, new_state)

    def on_delete_clicked(self):
        """Handle delete button click"""
        self.process_deleted.emit(self.process.id)

    # ========== HELPERS ==========

    def get_relative_time(self, timestamp) -> str:
        """Get relative time (e.g., 'Hace 2 días')"""
        try:
            if isinstance(timestamp, str):
                # Parse string to datetime
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            now = datetime.now()

            # Make both timezone-aware or both naive
            if timestamp.tzinfo is not None and now.tzinfo is None:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            elif timestamp.tzinfo is None and now.tzinfo is not None:
                timestamp = timestamp.replace(tzinfo=now.tzinfo)

            delta = now - timestamp

            if delta.days == 0:
                if delta.seconds < 60:
                    return "Hace unos segundos"
                elif delta.seconds < 3600:
                    minutes = delta.seconds // 60
                    return f"Hace {minutes} minuto(s)"
                else:
                    hours = delta.seconds // 3600
                    return f"Hace {hours} hora(s)"
            elif delta.days == 1:
                return "Hace 1 día"
            elif delta.days < 30:
                return f"Hace {delta.days} días"
            elif delta.days < 365:
                months = delta.days // 30
                return f"Hace {months} mes(es)"
            else:
                years = delta.days // 365
                return f"Hace {years} año(s)"
        except Exception as e:
            logger.error(f"Error calculating relative time: {e}")
            return "Fecha desconocida"
