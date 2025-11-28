# -*- coding: utf-8 -*-
"""
Image Gallery Window

Ventana principal del visor de galería de imágenes.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QWidget, QFrame,
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from src.controllers.image_gallery_controller import ImageGalleryController
from src.views.image_gallery.image_grid_widget import ImageGridWidget
from src.views.image_gallery.image_search_panel import ImageSearchPanel
from src.views.image_gallery.image_preview_dialog import ImagePreviewDialog

logger = logging.getLogger(__name__)


class ImageGalleryWindow(QDialog):
    """
    Ventana principal de la galería de imágenes

    Características:
    - Barra de búsqueda en tiempo real
    - Filtros por categoría, tags, favoritos
    - Grid de thumbnails (implementado en FASE 3)
    - Paginación
    - Estadísticas
    """

    # Señales
    image_selected = pyqtSignal(dict)  # Imagen seleccionada
    closed = pyqtSignal()  # Ventana cerrada

    def __init__(self, controller: ImageGalleryController, parent=None):
        """
        Inicializar ventana de galería

        Args:
            controller: ImageGalleryController instance
            parent: Widget padre
        """
        super().__init__(parent)

        self.controller = controller

        self.init_ui()
        self.connect_signals()
        self.load_initial_data()

        logger.info("ImageGalleryWindow initialized")

    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("Galería de Imágenes")
        self.setModal(False)
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

        # Aplicar estilos
        self.setStyleSheet(self._get_stylesheet())

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Barra de filtros
        filters_bar = self._create_filters_bar()
        main_layout.addWidget(filters_bar)

        # Área de contenido (grid de imágenes)
        content_area = self._create_content_area()
        main_layout.addWidget(content_area, stretch=1)

        # Footer (paginación y stats)
        footer = self._create_footer()
        main_layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """
        Crear header con título y controles

        Returns:
            Widget de header
        """
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(70)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # Icono y título
        title_label = QLabel("🖼️ Galería de Imágenes")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)

        layout.addWidget(title_label)
        layout.addStretch()

        # Botón de configuración
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("iconButton")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setToolTip("Configuración de galería")
        self.settings_btn.clicked.connect(self._show_settings)

        # Botón cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setToolTip("Cerrar galería")
        self.close_btn.clicked.connect(self.close)

        layout.addWidget(self.settings_btn)
        layout.addWidget(self.close_btn)

        return header

    def _create_filters_bar(self) -> QWidget:
        """
        Crear barra de filtros y búsqueda (FASE 4: Advanced Search Panel)

        Returns:
            Widget de filtros
        """
        # Usar el nuevo ImageSearchPanel con filtros avanzados
        self.search_panel = ImageSearchPanel(db_manager=self.controller.db, parent=self)

        # Conectar señales del panel de búsqueda
        self.search_panel.filters_changed.connect(self._on_filters_changed)
        self.search_panel.search_requested.connect(self._on_search_requested)
        self.search_panel.filters_cleared.connect(self._on_filters_cleared)

        return self.search_panel

    def _create_content_area(self) -> QWidget:
        """
        Crear área de contenido principal

        Returns:
            Widget de contenido
        """
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area para el grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Grid widget
        self.grid_widget = ImageGridWidget(controller=self.controller, parent=self)

        # Conectar señales del grid
        self.grid_widget.card_clicked.connect(self._on_card_clicked)
        self.grid_widget.preview_requested.connect(self._on_preview_requested)
        self.grid_widget.copy_requested.connect(self._on_copy_requested)
        self.grid_widget.edit_requested.connect(self._on_edit_requested)
        self.grid_widget.delete_requested.connect(self._on_delete_requested)

        self.scroll_area.setWidget(self.grid_widget)
        content_layout.addWidget(self.scroll_area)

        return content_widget

    def _create_footer(self) -> QWidget:
        """
        Crear footer con paginación y estadísticas

        Returns:
            Widget de footer
        """
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(60)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 10, 20, 10)

        # Estadísticas
        self.stats_label = QLabel("Total: 0 imágenes")
        self.stats_label.setObjectName("statsLabel")

        # Paginación
        pagination = QWidget()
        pagination_layout = QHBoxLayout(pagination)
        pagination_layout.setContentsMargins(0, 0, 0, 0)
        pagination_layout.setSpacing(5)

        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.setFixedWidth(100)
        self.prev_btn.clicked.connect(self._previous_page)

        self.page_label = QLabel("Página 1 de 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(120)

        self.next_btn = QPushButton("Siguiente ▶")
        self.next_btn.setFixedWidth(100)
        self.next_btn.clicked.connect(self._next_page)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)

        layout.addWidget(self.stats_label)
        layout.addStretch()
        layout.addWidget(pagination)

        return footer

    def connect_signals(self):
        """Conectar señales del controller"""
        self.controller.images_loaded.connect(self._on_images_loaded)
        self.controller.page_changed.connect(self._on_page_changed)
        self.controller.loading_started.connect(self._on_loading_started)
        self.controller.loading_finished.connect(self._on_loading_finished)
        self.controller.error_occurred.connect(self._on_error)

    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            # Cargar primera página (categorías y tags ya se cargan en ImageSearchPanel)
            self.controller.load_images(page=1)

        except Exception as e:
            logger.error(f"Error loading initial data: {e}", exc_info=True)
            self._show_error(f"Error al cargar datos: {str(e)}")

    def _on_filters_changed(self, filters: dict):
        """
        Handler cuando cambian los filtros (FASE 4)

        Args:
            filters: Diccionario con filtros activos
        """
        logger.debug(f"Filters changed in window: {filters}")

        # Aplicar filtros al controller (unpack dict)
        self.controller.apply_filters(**filters)

    def _on_search_requested(self):
        """Handler cuando se solicita búsqueda inmediata (botón Buscar Ahora)"""
        logger.info("Immediate search requested")
        # Los filtros ya están aplicados por _on_filters_changed
        # Solo forzar recarga
        self.controller.load_images(page=1)

    def _on_filters_cleared(self):
        """Handler cuando se limpian todos los filtros"""
        logger.info("All filters cleared")
        # Limpiar en controller
        self.controller.clear_filters()

    def _on_images_loaded(self, images: list):
        """
        Handler cuando se cargan imágenes

        Args:
            images: Lista de imágenes cargadas
        """
        logger.info(f"Images loaded in window: {len(images)} items")

        # Actualizar estadísticas
        pagination_info = self.controller.get_pagination_info()
        total = pagination_info['total_items']
        self.stats_label.setText(f"Total: {total} imágenes")

        # Actualizar contador de resultados en search panel (FASE 4)
        if hasattr(self, 'search_panel'):
            self.search_panel.set_result_count(total)

        # Actualizar grid con imágenes
        self.grid_widget.load_images(images)

    def _on_page_changed(self, current_page: int, total_pages: int):
        """
        Handler cuando cambia la página

        Args:
            current_page: Página actual
            total_pages: Total de páginas
        """
        self.page_label.setText(f"Página {current_page} de {total_pages}")

        # Habilitar/deshabilitar botones
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def _previous_page(self):
        """Ir a página anterior"""
        self.controller.previous_page()

    def _next_page(self):
        """Ir a página siguiente"""
        self.controller.next_page()

    def _on_loading_started(self):
        """Handler cuando inicia carga"""
        self.setCursor(Qt.CursorShape.WaitCursor)
        logger.debug("Loading started")

    def _on_loading_finished(self):
        """Handler cuando termina carga"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        logger.debug("Loading finished")

    def _on_error(self, message: str):
        """
        Handler de errores

        Args:
            message: Mensaje de error
        """
        self._show_error(message)

    def _show_error(self, message: str):
        """
        Mostrar mensaje de error

        Args:
            message: Mensaje
        """
        QMessageBox.critical(self, "Error", message)

    def _on_item_deleted_from_preview(self, item_id: int):
        """
        Handler cuando se elimina un item desde el preview dialog

        Args:
            item_id: ID del item eliminado
        """
        logger.info(f"Item deleted from preview: {item_id}")
        # Recargar página actual para reflejar cambios
        self.controller.load_images(self.controller.current_page)

    def _on_favorite_toggled_from_preview(self, item_id: int, is_favorite: bool):
        """
        Handler cuando se toggle favorito desde preview

        Args:
            item_id: ID del item
            is_favorite: Nuevo estado de favorito
        """
        logger.info(f"Favorite toggled from preview: {item_id} -> {is_favorite}")
        # Recargar página actual para reflejar cambios
        self.controller.load_images(self.controller.current_page)

    def _on_item_updated_from_preview(self, item_id: int):
        """
        Handler cuando se actualizan metadatos desde preview

        Args:
            item_id: ID del item actualizado
        """
        logger.info(f"Item metadata updated from preview: {item_id}")
        # Recargar página actual para reflejar cambios
        self.controller.load_images(self.controller.current_page)

    def _show_settings(self):
        """Mostrar configuración (placeholder)"""
        QMessageBox.information(
            self,
            "Configuración",
            "Panel de configuración de galería\nSe implementará en FASE 6"
        )

    def _on_card_clicked(self, item_data: dict):
        """
        Handler cuando se hace click en una card

        Args:
            item_data: Datos del item
        """
        logger.info(f"Card clicked: {item_data.get('label')}")
        # Emitir señal para notificar a otros componentes
        self.image_selected.emit(item_data)

    def _on_preview_requested(self, item_data: dict):
        """
        Handler cuando se solicita preview (FASE 5)

        Args:
            item_data: Datos del item
        """
        logger.info(f"Preview requested: {item_data.get('label')}")

        try:
            # Crear y mostrar preview dialog
            preview_dialog = ImagePreviewDialog(
                item_data=item_data,
                controller=self.controller,
                parent=self
            )

            # Conectar señales
            preview_dialog.item_deleted.connect(self._on_item_deleted_from_preview)
            preview_dialog.favorite_toggled.connect(self._on_favorite_toggled_from_preview)
            preview_dialog.item_updated.connect(self._on_item_updated_from_preview)

            # Mostrar modal
            preview_dialog.exec()

        except Exception as e:
            logger.error(f"Error opening preview: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al abrir preview:\n{str(e)}"
            )

    def _on_copy_requested(self, item_data: dict):
        """
        Handler cuando se solicita copiar

        Args:
            item_data: Datos del item
        """
        logger.info(f"Copy requested: {item_data.get('label')}")

        # Copiar ruta al portapapeles
        import pyperclip
        content = item_data.get('content', '')

        if content:
            try:
                pyperclip.copy(content)
                logger.debug(f"Copied to clipboard: {content}")

                # Mostrar feedback
                QMessageBox.information(
                    self,
                    "Copiado",
                    f"Ruta copiada al portapapeles:\n\n{content}"
                )
            except Exception as e:
                logger.error(f"Error copying to clipboard: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al copiar al portapapeles:\n{str(e)}"
                )

    def _on_edit_requested(self, item_data: dict):
        """
        Handler cuando se solicita editar

        Args:
            item_data: Datos del item
        """
        logger.info(f"Edit requested: {item_data.get('label')}")
        # TODO: Abrir EditMetadataDialog en FASE 6
        QMessageBox.information(
            self,
            "Editar",
            f"Edición de metadata se implementará en FASE 6\n\nItem: {item_data.get('label')}"
        )

    def _on_delete_requested(self, item_data: dict):
        """
        Handler cuando se solicita eliminar

        Args:
            item_data: Datos del item
        """
        logger.info(f"Delete requested: {item_data.get('label')}")

        # Confirmar eliminación
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar esta imagen?\n\n{item_data.get('label')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                item_id = item_data.get('id')
                if item_id:
                    # Eliminar desde BD
                    self.controller.db.delete_item(item_id)
                    logger.info(f"Item deleted: ID {item_id}")

                    # Recargar página actual
                    self.controller.load_images(self.controller.current_page)

                    QMessageBox.information(
                        self,
                        "Eliminado",
                        "Imagen eliminada exitosamente"
                    )
            except Exception as e:
                logger.error(f"Error deleting item: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al eliminar imagen:\n{str(e)}"
                )

    def closeEvent(self, event):
        """Override close event"""
        self.closed.emit()
        super().closeEvent(event)

    def _get_stylesheet(self) -> str:
        """
        Obtener stylesheet de la ventana

        Returns:
            String con CSS
        """
        return """
            QDialog {
                background-color: #1e1e1e;
                color: #cccccc;
            }

            #header {
                background-color: #252525;
                border-bottom: 2px solid #007acc;
            }

            #filtersBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #3d3d3d;
            }

            #footer {
                background-color: #252525;
                border-top: 1px solid #3d3d3d;
            }

            QLabel {
                color: #cccccc;
            }

            #statsLabel {
                font-weight: bold;
                color: #007acc;
            }

            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 10pt;
            }

            QLineEdit:focus {
                border: 1px solid #007acc;
            }

            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 10pt;
            }

            QComboBox:focus {
                border: 1px solid #007acc;
            }

            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #cccccc;
                margin-right: 5px;
            }

            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
                border: 1px solid #3d3d3d;
            }

            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #005a9e;
            }

            QPushButton:pressed {
                background-color: #004578;
            }

            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666666;
            }

            QPushButton:checked {
                background-color: #feca57;
                color: #000000;
            }

            #iconButton {
                background-color: #3d3d3d;
                font-size: 14pt;
            }

            #iconButton:hover {
                background-color: #4d4d4d;
            }

            #closeButton {
                background-color: #e74c3c;
                font-size: 14pt;
            }

            #closeButton:hover {
                background-color: #c0392b;
            }

            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }

            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #007acc;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
