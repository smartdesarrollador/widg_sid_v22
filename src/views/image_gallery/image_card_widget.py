# -*- coding: utf-8 -*-
"""
Image Card Widget

Widget individual para mostrar una imagen en el grid con:
- Thumbnail
- Nombre del item
- Categoría e icono
- Tags
- Overlay con acciones al hover
"""

import logging
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QCursor, QPalette, QColor

logger = logging.getLogger(__name__)


class ImageCardWidget(QWidget):
    """
    Widget de tarjeta para mostrar una imagen

    Estructura:
    ┌─────────────────────────┐
    │  [Thumbnail 150x150]    │
    │                         │
    │  Nombre del item        │
    │  📁 Categoría           │
    │  🏷️ tag1, tag2, tag3    │
    └─────────────────────────┘

    Al hacer hover:
    ┌─────────────────────────┐
    │  [Thumbnail con overlay]│
    │  [👁️] [📋] [✏️] [❌]    │
    │                         │
    │  Nombre del item        │
    │  📁 Categoría           │
    │  🏷️ tag1, tag2, tag3    │
    └─────────────────────────┘
    """

    # Señales
    clicked = pyqtSignal(dict)  # Item data
    preview_requested = pyqtSignal(dict)  # Preview imagen
    copy_requested = pyqtSignal(dict)  # Copiar al portapapeles
    edit_requested = pyqtSignal(dict)  # Editar item
    delete_requested = pyqtSignal(dict)  # Eliminar item

    def __init__(self, item_data: Dict, thumbnail: Optional[QPixmap] = None, parent=None):
        """
        Inicializar card widget

        Args:
            item_data: Dict con datos del item
            thumbnail: QPixmap del thumbnail (opcional)
            parent: Widget padre
        """
        super().__init__(parent)

        self.item_data = item_data
        self.thumbnail = thumbnail
        self.is_hovered = False

        self.init_ui()

    def init_ui(self):
        """Inicializar interfaz"""
        self.setFixedSize(180, 260)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Aplicar estilos
        self.setStyleSheet("""
            ImageCardWidget {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
            ImageCardWidget:hover {
                border: 2px solid #007acc;
                background-color: #353535;
            }
        """)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Contenedor del thumbnail con overlay
        self.thumbnail_container = self._create_thumbnail_container()
        main_layout.addWidget(self.thumbnail_container)

        # Nombre del item
        self.name_label = QLabel(self.item_data.get('label', 'Sin nombre'))
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        name_font = QFont()
        name_font.setPointSize(9)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #ffffff; background: transparent;")
        main_layout.addWidget(self.name_label)

        # Categoría
        category_name = self.item_data.get('category_name', 'Sin categoría')
        category_icon = self.item_data.get('category_icon', '📁')
        self.category_label = QLabel(f"{category_icon} {category_name}")
        self.category_label.setStyleSheet("color: #888888; font-size: 8pt; background: transparent;")
        main_layout.addWidget(self.category_label)

        # Tags
        tags = self.item_data.get('tags', [])
        if tags:
            tags_text = ', '.join(tags[:3])  # Máximo 3 tags
            if len(tags) > 3:
                tags_text += f" +{len(tags) - 3}"
            self.tags_label = QLabel(f"🏷️ {tags_text}")
            self.tags_label.setWordWrap(True)
            self.tags_label.setMaximumHeight(35)
            self.tags_label.setStyleSheet("color: #666666; font-size: 7pt; background: transparent;")
            main_layout.addWidget(self.tags_label)
        else:
            # Spacer si no hay tags
            spacer = QLabel("")
            spacer.setMaximumHeight(35)
            main_layout.addWidget(spacer)

        main_layout.addStretch()

    def _create_thumbnail_container(self) -> QWidget:
        """
        Crear contenedor del thumbnail con overlay

        Returns:
            Widget contenedor
        """
        container = QWidget()
        container.setFixedSize(164, 164)

        # Layout del contenedor (para overlay)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(164, 164)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)

        # Mostrar thumbnail o placeholder
        if self.thumbnail and not self.thumbnail.isNull():
            scaled = self.thumbnail.scaled(
                164, 164,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled)
        else:
            # Placeholder
            self.thumbnail_label.setText("🖼️")
            placeholder_font = QFont()
            placeholder_font.setPointSize(32)
            self.thumbnail_label.setFont(placeholder_font)
            self.thumbnail_label.setStyleSheet("""
                QLabel {
                    background-color: #1e1e1e;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    color: #555555;
                }
            """)

        layout.addWidget(self.thumbnail_label)

        # Overlay con acciones (inicialmente oculto)
        self.overlay = self._create_overlay()
        self.overlay.hide()
        layout.addWidget(self.overlay)

        return container

    def _create_overlay(self) -> QWidget:
        """
        Crear overlay con botones de acción

        Returns:
            Widget overlay
        """
        overlay = QFrame()
        overlay.setFixedSize(164, 164)
        overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 4px;
            }
        """)

        # Layout del overlay
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(10, 10, 10, 10)

        # Spacer superior
        overlay_layout.addStretch()

        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        # Botón Preview
        preview_btn = QPushButton("👁️")
        preview_btn.setFixedSize(35, 35)
        preview_btn.setToolTip("Vista previa")
        preview_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        preview_btn.setStyleSheet(self._get_action_button_style())
        preview_btn.clicked.connect(self._on_preview_clicked)
        buttons_layout.addWidget(preview_btn)

        # Botón Copiar
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(35, 35)
        copy_btn.setToolTip("Copiar ruta")
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setStyleSheet(self._get_action_button_style())
        copy_btn.clicked.connect(self._on_copy_clicked)
        buttons_layout.addWidget(copy_btn)

        # Botón Editar
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(35, 35)
        edit_btn.setToolTip("Editar item")
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.setStyleSheet(self._get_action_button_style())
        edit_btn.clicked.connect(self._on_edit_clicked)
        buttons_layout.addWidget(edit_btn)

        # Botón Eliminar
        delete_btn = QPushButton("❌")
        delete_btn.setFixedSize(35, 35)
        delete_btn.setToolTip("Eliminar")
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet(self._get_action_button_style("#e74c3c"))
        delete_btn.clicked.connect(self._on_delete_clicked)
        buttons_layout.addWidget(delete_btn)

        overlay_layout.addLayout(buttons_layout)

        # Spacer inferior
        overlay_layout.addStretch()

        return overlay

    def _get_action_button_style(self, hover_color: str = "#007acc") -> str:
        """
        Obtener estilo para botones de acción

        Args:
            hover_color: Color en hover

        Returns:
            String con CSS
        """
        return f"""
            QPushButton {{
                background-color: rgba(45, 45, 45, 200);
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 14pt;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border: 1px solid {hover_color};
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 200);
            }}
        """

    def enterEvent(self, event):
        """Override enter event para mostrar overlay"""
        self.is_hovered = True
        if self.overlay:
            self.overlay.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Override leave event para ocultar overlay"""
        self.is_hovered = False
        if self.overlay:
            self.overlay.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Override mouse press para emitir señal clicked"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Solo emitir si no se hizo click en overlay
            if not self.is_hovered or not self.overlay.isVisible():
                self.clicked.emit(self.item_data)
        super().mousePressEvent(event)

    def _on_preview_clicked(self):
        """Handler para botón preview"""
        logger.debug(f"Preview requested: {self.item_data.get('label')}")
        self.preview_requested.emit(self.item_data)

    def _on_copy_clicked(self):
        """Handler para botón copiar"""
        logger.debug(f"Copy requested: {self.item_data.get('label')}")
        self.copy_requested.emit(self.item_data)

    def _on_edit_clicked(self):
        """Handler para botón editar"""
        logger.debug(f"Edit requested: {self.item_data.get('label')}")
        self.edit_requested.emit(self.item_data)

    def _on_delete_clicked(self):
        """Handler para botón eliminar"""
        logger.debug(f"Delete requested: {self.item_data.get('label')}")
        self.delete_requested.emit(self.item_data)

    def set_thumbnail(self, pixmap: QPixmap):
        """
        Actualizar thumbnail

        Args:
            pixmap: Nuevo thumbnail
        """
        if pixmap and not pixmap.isNull():
            self.thumbnail = pixmap
            scaled = pixmap.scaled(
                164, 164,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled)

    def get_item_data(self) -> Dict:
        """
        Obtener datos del item

        Returns:
            Dict con datos
        """
        return self.item_data
