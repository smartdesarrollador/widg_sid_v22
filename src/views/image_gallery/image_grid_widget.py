# -*- coding: utf-8 -*-
"""
Image Grid Widget

Widget contenedor que muestra un grid de ImageCardWidgets con:
- Layout tipo flow (adapta a ancho disponible)
- Lazy loading de thumbnails
- Scroll infinito
"""

import logging
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap

from src.views.image_gallery.image_card_widget import ImageCardWidget

logger = logging.getLogger(__name__)


class FlowLayout(QVBoxLayout):
    """
    Layout personalizado tipo flow que organiza items en filas
    adaptándose al ancho disponible
    """

    def __init__(self, parent=None, margin=10, spacing=10):
        super().__init__(parent)
        self.margin = margin
        self.spacing = spacing
        self.rows = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def add_widget_to_flow(self, widget):
        """Agregar widget al flow layout"""
        # Por ahora usamos grid simple (se optimizará en futuras versiones)
        self.addWidget(widget)


class ImageGridWidget(QWidget):
    """
    Widget de grid para mostrar imágenes en cards

    Características:
    - Grid responsive (adapta columnas al ancho)
    - Lazy loading de thumbnails
    - Señales para interacción con cards
    """

    # Señales
    card_clicked = pyqtSignal(dict)  # Item clickeado
    preview_requested = pyqtSignal(dict)  # Preview solicitado
    copy_requested = pyqtSignal(dict)  # Copiar solicitado
    edit_requested = pyqtSignal(dict)  # Editar solicitado
    delete_requested = pyqtSignal(dict)  # Eliminar solicitado
    load_more_requested = pyqtSignal()  # Cargar más (scroll infinito)

    def __init__(self, controller, parent=None):
        """
        Inicializar grid widget

        Args:
            controller: ImageGalleryController instance
            parent: Widget padre
        """
        super().__init__(parent)

        self.controller = controller
        self.cards = []
        self.images_data = []
        self.card_width = 180
        self.card_height = 260
        self.spacing = 15

        self.init_ui()

    def init_ui(self):
        """Inicializar interfaz"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # Grid layout para las cards
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(self.spacing)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        main_layout.addLayout(self.grid_layout)

        # Spacer al final
        main_layout.addStretch()

        # Timer para lazy loading
        self.lazy_timer = QTimer()
        self.lazy_timer.setSingleShot(True)
        self.lazy_timer.timeout.connect(self._load_visible_thumbnails)

    def load_images(self, images_data: List[Dict]):
        """
        Cargar imágenes en el grid

        Args:
            images_data: Lista de dicts con datos de imágenes
        """
        # Limpiar grid actual
        self.clear()

        self.images_data = images_data

        if not images_data:
            # Mostrar mensaje de "no hay imágenes"
            self._show_empty_message()
            return

        # Calcular columnas según ancho disponible
        columns = self._calculate_columns()

        logger.info(f"Loading {len(images_data)} images in grid ({columns} columns)")

        # Crear cards
        for index, item_data in enumerate(images_data):
            row = index // columns
            col = index % columns

            # Crear card sin thumbnail (lazy loading)
            card = ImageCardWidget(item_data=item_data, thumbnail=None, parent=self)

            # Conectar señales
            card.clicked.connect(self.card_clicked.emit)
            card.preview_requested.connect(self.preview_requested.emit)
            card.copy_requested.connect(self.copy_requested.emit)
            card.edit_requested.connect(self.edit_requested.emit)
            card.delete_requested.connect(self.delete_requested.emit)

            # Agregar al grid
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

        logger.debug(f"Created {len(self.cards)} cards")

        # Iniciar lazy loading después de un momento
        self.lazy_timer.start(100)

    def _calculate_columns(self) -> int:
        """
        Calcular número de columnas según ancho disponible

        Returns:
            Número de columnas
        """
        # Obtener ancho disponible
        available_width = self.width()

        if available_width < 200:
            # Ancho mínimo, usar ancho del padre
            parent = self.parentWidget()
            if parent:
                available_width = parent.width()
            else:
                available_width = 800  # Fallback

        # Calcular columnas
        # card_width + spacing entre cards
        card_total_width = self.card_width + self.spacing

        # Restar márgenes
        usable_width = available_width - 40  # Márgenes del layout

        columns = max(1, usable_width // card_total_width)

        logger.debug(f"Grid columns: {columns} (width: {available_width}px)")

        return columns

    def _load_visible_thumbnails(self):
        """Cargar thumbnails de cards visibles (lazy loading)"""
        try:
            logger.debug("Loading visible thumbnails...")

            loaded_count = 0

            for card in self.cards[:20]:  # Primeras 20 cards
                item_data = card.get_item_data()
                image_path = item_data.get('content')

                if image_path:
                    # Obtener thumbnail desde controller
                    thumbnail = self.controller.get_thumbnail(image_path, size='medium')

                    if thumbnail:
                        card.set_thumbnail(thumbnail)
                        loaded_count += 1

            logger.info(f"Loaded {loaded_count} thumbnails")

        except Exception as e:
            logger.error(f"Error loading thumbnails: {e}", exc_info=True)

    def load_more_thumbnails(self):
        """Cargar más thumbnails (para scroll infinito)"""
        # TODO: Implementar en versión futura
        pass

    def clear(self):
        """Limpiar grid"""
        # Eliminar todas las cards
        for card in self.cards:
            card.deleteLater()

        self.cards.clear()

        # Limpiar layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        logger.debug("Grid cleared")

    def _show_empty_message(self):
        """Mostrar mensaje cuando no hay imágenes"""
        # Limpiar primero
        self.clear()

        # Crear mensaje
        message = QLabel("📭 No se encontraron imágenes")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14pt;
                padding: 100px;
                background: transparent;
            }
        """)

        self.grid_layout.addWidget(message, 0, 0)

    def refresh(self):
        """Refrescar grid con imágenes actuales"""
        if self.images_data:
            self.load_images(self.images_data)

    def get_card_count(self) -> int:
        """Obtener número de cards en el grid"""
        return len(self.cards)

    def resizeEvent(self, event):
        """Override resize event para recalcular columnas"""
        super().resizeEvent(event)

        # Recalcular grid cuando cambia el tamaño
        if self.images_data:
            # Usar timer para evitar múltiples recalculos
            if not hasattr(self, 'resize_timer'):
                self.resize_timer = QTimer()
                self.resize_timer.setSingleShot(True)
                self.resize_timer.timeout.connect(self.refresh)

            self.resize_timer.stop()
            self.resize_timer.start(300)
