"""
Process Step Config Dialog - Dialog para editar configuracion de un step

Permite configurar:
- Custom label
- Is optional
- Wait for confirmation
- Notes
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QCheckBox,
                             QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.process import ProcessStep

logger = logging.getLogger(__name__)


class ProcessStepConfigDialog(QDialog):
    """Dialog para configurar un step del proceso"""

    # Signal emitted when configuration is saved
    config_saved = pyqtSignal(object)  # ProcessStep

    def __init__(self, step: ProcessStep, parent=None):
        """
        Initialize dialog

        Args:
            step: ProcessStep to configure
            parent: Parent widget
        """
        super().__init__(parent)
        self.step = step
        self.init_ui()
        self.load_step_data()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Configurar Step")
        self.setModal(True)
        self.setFixedSize(500, 450)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title = QLabel("Configuracion del Step")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 14pt;
                font-weight: bold;
                padding-bottom: 10px;
            }
        """)
        main_layout.addWidget(title)

        # Item info (read-only)
        info_group = QGroupBox("Informacion del Item")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_group)

        # Item label
        item_label_widget = QLabel(f"Label: {self.step.item_label}")
        item_label_widget.setStyleSheet("color: #ffffff; padding: 3px;")
        info_layout.addWidget(item_label_widget)

        # Item type
        item_type_widget = QLabel(f"Tipo: {self.step.item_type}")
        item_type_widget.setStyleSheet("color: #888888; padding: 3px;")
        info_layout.addWidget(item_type_widget)

        main_layout.addWidget(info_group)

        # Custom label
        custom_label_layout = QVBoxLayout()
        custom_label_label = QLabel("Label Personalizado:")
        custom_label_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        custom_label_layout.addWidget(custom_label_label)

        self.custom_label_input = QLineEdit()
        self.custom_label_input.setPlaceholderText("Dejar vacio para usar el label original del item...")
        self.custom_label_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
        custom_label_layout.addWidget(self.custom_label_input)
        main_layout.addLayout(custom_label_layout)

        # Checkboxes
        checkbox_group = QGroupBox("Opciones")
        checkbox_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        checkbox_layout = QVBoxLayout(checkbox_group)

        # Is optional
        self.optional_checkbox = QCheckBox("Step Opcional")
        self.optional_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #ff6b00;
                border: 2px solid #ff6b00;
                border-radius: 3px;
            }
        """)
        self.optional_checkbox.setToolTip("Si es opcional, el proceso continua aunque este step falle")
        checkbox_layout.addWidget(self.optional_checkbox)

        # Wait for confirmation
        self.wait_checkbox = QCheckBox("Esperar Confirmacion")
        self.wait_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #ffa500;
                border: 2px solid #ffa500;
                border-radius: 3px;
            }
        """)
        self.wait_checkbox.setToolTip("Pausar la ejecucion antes de este step para pedir confirmacion")
        checkbox_layout.addWidget(self.wait_checkbox)

        # Is enabled
        self.enabled_checkbox = QCheckBox("Step Habilitado")
        self.enabled_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #00ff88;
                border: 2px solid #00ff88;
                border-radius: 3px;
            }
        """)
        self.enabled_checkbox.setToolTip("Si esta deshabilitado, este step se omitira durante la ejecucion")
        checkbox_layout.addWidget(self.enabled_checkbox)

        main_layout.addWidget(checkbox_group)

        # Notes
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Notas:")
        notes_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        notes_layout.addWidget(notes_label)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionales para este step...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
        notes_layout.addWidget(self.notes_input)
        main_layout.addLayout(notes_layout)

        main_layout.addStretch()

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Guardar")
        save_btn.setFixedSize(100, 35)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        save_btn.clicked.connect(self.save_config)
        buttons_layout.addWidget(save_btn)

        main_layout.addLayout(buttons_layout)

        # Apply global styles
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def load_step_data(self):
        """Load step data into form"""
        # Custom label
        if self.step.custom_label:
            self.custom_label_input.setText(self.step.custom_label)

        # Checkboxes
        self.optional_checkbox.setChecked(self.step.is_optional)
        self.wait_checkbox.setChecked(self.step.wait_for_confirmation)
        self.enabled_checkbox.setChecked(self.step.is_enabled)

        # Notes
        if self.step.notes:
            self.notes_input.setPlainText(self.step.notes)

    def save_config(self):
        """Save configuration to step"""
        try:
            # Update step with form data
            custom_label = self.custom_label_input.text().strip()
            self.step.custom_label = custom_label if custom_label else None

            self.step.is_optional = self.optional_checkbox.isChecked()
            self.step.wait_for_confirmation = self.wait_checkbox.isChecked()
            self.step.is_enabled = self.enabled_checkbox.isChecked()

            notes = self.notes_input.toPlainText().strip()
            self.step.notes = notes if notes else None

            logger.info(f"Step configuration saved: {self.step.get_display_label()}")

            # Emit signal
            self.config_saved.emit(self.step)

            # Close dialog
            self.accept()

        except Exception as e:
            logger.error(f"Error saving step configuration: {e}", exc_info=True)
            self.reject()
