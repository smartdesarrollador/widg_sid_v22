# -*- coding: utf-8 -*-
"""
Edit Metadata Dialog

Diálogo para editar metadatos de una imagen.

Permite editar:
- Nombre del item
- Categoría
- Tags
- Descripción
- Estado de favorito
"""

import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit, QCheckBox,
    QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class EditMetadataDialog(QDialog):
    """
    Diálogo para editar metadatos de imagen

    Campos editables:
    - Nombre
    - Categoría
    - Tags
    - Descripción
    - Favorito
    """

    # Señales
    metadata_updated = pyqtSignal(int, dict)  # item_id, updated_data

    def __init__(self, item_data: Dict, categories: List[Dict], parent=None):
        """
        Inicializar diálogo de edición

        Args:
            item_data: Datos actuales del item
            categories: Lista de categorías disponibles
            parent: Widget padre
        """
        super().__init__(parent)

        self.item_data = item_data
        self.categories = categories
        self.item_id = item_data.get('id')

        self.init_ui()
        self.load_current_data()

        logger.info(f"EditMetadataDialog opened for item: {self.item_id}")

    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Editar Metadatos")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("✏️ Editar Metadatos")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        main_layout.addWidget(separator)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Campo: Nombre
        label_name = QLabel("Nombre:")
        label_name.setObjectName("formLabel")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre descriptivo de la imagen...")
        form_layout.addRow(label_name, self.name_input)

        # Campo: Categoría
        label_category = QLabel("Categoría:")
        label_category.setObjectName("formLabel")
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(250)
        self._populate_categories()
        form_layout.addRow(label_category, self.category_combo)

        # Campo: Tags
        label_tags = QLabel("Tags:")
        label_tags.setObjectName("formLabel")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3...")
        form_layout.addRow(label_tags, self.tags_input)

        # Campo: Descripción
        label_description = QLabel("Descripción:")
        label_description.setObjectName("formLabel")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descripción opcional...")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow(label_description, self.description_input)

        # Campo: Favorito
        label_favorite = QLabel("Favorito:")
        label_favorite.setObjectName("formLabel")
        self.favorite_checkbox = QCheckBox("Marcar como favorito")
        form_layout.addRow(label_favorite, self.favorite_checkbox)

        main_layout.addLayout(form_layout)

        # Spacer
        main_layout.addStretch()

        # Información de la ruta (solo lectura)
        path_label = QLabel("Ruta:")
        path_label.setObjectName("formLabel")
        self.path_display = QLabel(self.item_data.get('content', 'N/A'))
        self.path_display.setWordWrap(True)
        self.path_display.setObjectName("pathDisplay")
        self.path_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        path_layout = QHBoxLayout()
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_display, stretch=1)
        main_layout.addLayout(path_layout)

        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setObjectName("separator")
        main_layout.addWidget(separator2)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("💾 Guardar")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.clicked.connect(self.save_changes)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)

        main_layout.addLayout(buttons_layout)

        # Estilos
        self.setStyleSheet(self._get_stylesheet())

    def _populate_categories(self):
        """Poblar combo de categorías"""
        self.category_combo.clear()

        for category in self.categories:
            icon = category.get('icon', '📁')
            name = category.get('name', 'Sin nombre')
            cat_id = category.get('id')

            display_text = f"{icon} {name}"
            self.category_combo.addItem(display_text, cat_id)

    def load_current_data(self):
        """Cargar datos actuales del item en el formulario"""
        try:
            # Nombre
            current_name = self.item_data.get('label', '')
            self.name_input.setText(current_name)

            # Categoría
            current_category_id = self.item_data.get('category_id')
            if current_category_id:
                # Buscar índice de la categoría
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == current_category_id:
                        self.category_combo.setCurrentIndex(i)
                        break

            # Tags
            current_tags = self.item_data.get('tags', [])
            if current_tags:
                tags_text = ', '.join(current_tags)
                self.tags_input.setText(tags_text)

            # Descripción
            current_description = self.item_data.get('description', '')
            if current_description:
                self.description_input.setPlainText(current_description)

            # Favorito
            is_favorite = self.item_data.get('is_favorite', False)
            self.favorite_checkbox.setChecked(is_favorite)

            logger.debug(f"Loaded current data for item {self.item_id}")

        except Exception as e:
            logger.error(f"Error loading current data: {e}", exc_info=True)

    def save_changes(self):
        """Guardar cambios"""
        try:
            # Validar nombre
            new_name = self.name_input.text().strip()
            if not new_name:
                QMessageBox.warning(
                    self,
                    "Validación",
                    "El nombre no puede estar vacío"
                )
                self.name_input.setFocus()
                return

            # Recopilar datos actualizados
            updated_data = {}

            # Nombre
            if new_name != self.item_data.get('label'):
                updated_data['label'] = new_name

            # Categoría
            new_category_id = self.category_combo.currentData()
            if new_category_id != self.item_data.get('category_id'):
                updated_data['category_id'] = new_category_id

            # Tags
            tags_text = self.tags_input.text().strip()
            if tags_text:
                new_tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            else:
                new_tags = []

            current_tags = self.item_data.get('tags', [])
            if new_tags != current_tags:
                updated_data['tags'] = new_tags

            # Descripción
            new_description = self.description_input.toPlainText().strip()
            if new_description != self.item_data.get('description', ''):
                updated_data['description'] = new_description

            # Favorito
            new_favorite = self.favorite_checkbox.isChecked()
            if new_favorite != self.item_data.get('is_favorite', False):
                updated_data['is_favorite'] = new_favorite

            # Si no hay cambios, informar
            if not updated_data:
                QMessageBox.information(
                    self,
                    "Sin Cambios",
                    "No se detectaron cambios en los metadatos"
                )
                return

            logger.info(f"Saving changes for item {self.item_id}: {updated_data}")

            # Emitir señal con datos actualizados
            self.metadata_updated.emit(self.item_id, updated_data)

            # Cerrar diálogo
            self.accept()

        except Exception as e:
            logger.error(f"Error saving changes: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar cambios:\n{str(e)}"
            )

    def _get_stylesheet(self) -> str:
        """Obtener stylesheet"""
        return """
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 9pt;
            }
            #formLabel {
                color: #cccccc;
                font-size: 9pt;
                font-weight: bold;
                min-width: 100px;
            }
            #pathDisplay {
                color: #888888;
                font-size: 8pt;
                font-style: italic;
            }
            #separator {
                background-color: #3d3d3d;
                max-height: 1px;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e0e0e0;
                font-size: 9pt;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #007acc;
            }
            QTextEdit {
                padding: 8px;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #007acc;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton#saveButton {
                background-color: #007acc;
                border: 1px solid #007acc;
                font-weight: bold;
            }
            QPushButton#saveButton:hover {
                background-color: #1e8ad6;
            }
        """
