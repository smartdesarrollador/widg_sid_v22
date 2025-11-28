# -*- coding: utf-8 -*-
"""
Image Preview Dialog

Diálogo de preview de imagen con zoom, pan y metadatos completos.

Características:
- Visor de imagen a tamaño completo
- Zoom in/out con rueda del mouse
- Pan con click y arrastre
- Panel lateral con metadatos
- Toolbar con acciones (copiar, favorito, eliminar, etc.)
"""

import logging
import os
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QMessageBox, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPixmap, QImage, QFont, QWheelEvent, QMouseEvent, QPainter

logger = logging.getLogger(__name__)


class ZoomableImageView(QGraphicsView):
    """
    Vista de imagen con zoom y pan

    Características:
    - Zoom con rueda del mouse
    - Pan con click y arrastre
    - Controles de zoom programáticos
    - Fit to window
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = None
        self.current_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Configuración
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(Qt.GlobalColor.black)

        # Variables para pan manual
        self.is_panning = False
        self.pan_start_pos = QPointF()

    def set_image(self, pixmap: QPixmap):
        """
        Establecer imagen a mostrar

        Args:
            pixmap: QPixmap con la imagen
        """
        if not pixmap or pixmap.isNull():
            logger.warning("Invalid pixmap provided to ZoomableImageView")
            return

        # Limpiar escena
        self.scene.clear()

        # Agregar pixmap
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        # Ajustar escena al tamaño de la imagen
        self.scene.setSceneRect(QRectF(pixmap.rect()))

        # Fit to window por defecto
        self.fit_to_window()

        logger.debug(f"Image set: {pixmap.width()}x{pixmap.height()}")

    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event para zoom"""
        # Factor de zoom
        zoom_factor = 1.15

        # Zoom in o zoom out según dirección de la rueda
        if event.angleDelta().y() > 0:
            # Zoom in
            self.zoom_in(zoom_factor)
        else:
            # Zoom out
            self.zoom_out(zoom_factor)

    def zoom_in(self, factor: float = 1.15):
        """Zoom in"""
        new_zoom = self.current_zoom * factor

        if new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.current_zoom = new_zoom
            logger.debug(f"Zoomed in: {self.current_zoom:.2f}x")

    def zoom_out(self, factor: float = 1.15):
        """Zoom out"""
        new_zoom = self.current_zoom / factor

        if new_zoom >= self.min_zoom:
            self.scale(1/factor, 1/factor)
            self.current_zoom = new_zoom
            logger.debug(f"Zoomed out: {self.current_zoom:.2f}x")

    def reset_zoom(self):
        """Reset zoom a 100%"""
        self.resetTransform()
        self.current_zoom = 1.0
        logger.debug("Zoom reset to 100%")

    def fit_to_window(self):
        """Ajustar imagen para que quepa en la ventana"""
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            # Calcular zoom actual después del fit
            view_rect = self.viewport().rect()
            scene_rect = self.pixmap_item.boundingRect()
            scale_x = view_rect.width() / scene_rect.width()
            scale_y = view_rect.height() / scene_rect.height()
            self.current_zoom = min(scale_x, scale_y)
            logger.debug(f"Fit to window: {self.current_zoom:.2f}x")

    def get_zoom_percentage(self) -> int:
        """Obtener porcentaje de zoom actual"""
        return int(self.current_zoom * 100)


class ImagePreviewDialog(QDialog):
    """
    Diálogo de preview de imagen con metadatos y acciones

    Layout:
    - Title bar: Nombre de la imagen + close
    - Main area: Image viewer (left) + Metadata panel (right)
    - Bottom: Actions toolbar
    """

    # Señales
    item_updated = pyqtSignal(int)  # item_id actualizado
    item_deleted = pyqtSignal(int)  # item_id eliminado
    favorite_toggled = pyqtSignal(int, bool)  # item_id, is_favorite

    def __init__(self, item_data: Dict, controller, parent=None):
        """
        Inicializar diálogo de preview

        Args:
            item_data: Diccionario con datos del item
            controller: ImageGalleryController
            parent: Widget padre
        """
        super().__init__(parent)

        self.item_data = item_data
        self.controller = controller
        self.image_path = item_data.get('content', '')

        self.init_ui()
        self.load_image()
        self.load_metadata()

        logger.info(f"ImagePreviewDialog opened: {item_data.get('label')}")

    def init_ui(self):
        """Inicializar interfaz"""
        # Configuración de ventana
        self.setWindowTitle(f"Preview - {self.item_data.get('label', 'Imagen')}")
        self.setModal(True)
        self.resize(1200, 800)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Content area (image viewer + metadata panel)
        content_widget = self._create_content_area()
        main_layout.addWidget(content_widget, stretch=1)

        # Actions toolbar
        toolbar = self._create_actions_toolbar()
        main_layout.addWidget(toolbar)

        # Estilos
        self.setStyleSheet(self._get_stylesheet())

    def _create_header(self) -> QWidget:
        """Crear header con título y botón cerrar"""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # Título
        title = QLabel(f"🖼️ {self.item_data.get('label', 'Imagen')}")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)

        layout.addWidget(title)
        layout.addStretch()

        # Botón cerrar
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(40, 40)
        close_btn.setToolTip("Cerrar preview")
        close_btn.clicked.connect(self.close)

        layout.addWidget(close_btn)

        return header

    def _create_content_area(self) -> QWidget:
        """Crear área de contenido con viewer y metadata panel"""
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Image viewer (izquierda)
        viewer_container = self._create_image_viewer()
        layout.addWidget(viewer_container, stretch=3)

        # Metadata panel (derecha)
        metadata_panel = self._create_metadata_panel()
        layout.addWidget(metadata_panel, stretch=1)

        return content

    def _create_image_viewer(self) -> QWidget:
        """Crear visor de imagen con zoom y controles"""
        container = QWidget()
        container.setObjectName("viewerContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Zoomable image view
        self.image_view = ZoomableImageView()
        self.image_view.setMinimumSize(600, 400)
        layout.addWidget(self.image_view, stretch=1)

        # Controles de zoom
        zoom_controls = self._create_zoom_controls()
        layout.addWidget(zoom_controls)

        return container

    def _create_zoom_controls(self) -> QWidget:
        """Crear controles de zoom"""
        controls = QFrame()
        controls.setObjectName("zoomControls")
        controls.setFixedHeight(50)

        layout = QHBoxLayout(controls)
        layout.setContentsMargins(10, 5, 10, 5)

        layout.addStretch()

        # Zoom out
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(40, 40)
        zoom_out_btn.setToolTip("Zoom out")
        zoom_out_btn.clicked.connect(lambda: self.image_view.zoom_out())

        # Zoom percentage
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setMinimumWidth(80)
        font = QFont()
        font.setPointSize(10)
        self.zoom_label.setFont(font)

        # Actualizar label cada segundo
        from PyQt6.QtCore import QTimer
        self.zoom_timer = QTimer()
        self.zoom_timer.timeout.connect(self._update_zoom_label)
        self.zoom_timer.start(100)  # Actualizar cada 100ms

        # Zoom in
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(40, 40)
        zoom_in_btn.setToolTip("Zoom in")
        zoom_in_btn.clicked.connect(lambda: self.image_view.zoom_in())

        # Reset zoom
        reset_btn = QPushButton("100%")
        reset_btn.setFixedSize(60, 40)
        reset_btn.setToolTip("Reset zoom")
        reset_btn.clicked.connect(self.image_view.reset_zoom)

        # Fit to window
        fit_btn = QPushButton("Ajustar")
        fit_btn.setFixedSize(80, 40)
        fit_btn.setToolTip("Ajustar a ventana")
        fit_btn.clicked.connect(self.image_view.fit_to_window)

        layout.addWidget(zoom_out_btn)
        layout.addWidget(self.zoom_label)
        layout.addWidget(zoom_in_btn)
        layout.addSpacing(20)
        layout.addWidget(reset_btn)
        layout.addWidget(fit_btn)
        layout.addStretch()

        return controls

    def _update_zoom_label(self):
        """Actualizar label de zoom"""
        if hasattr(self, 'image_view'):
            percentage = self.image_view.get_zoom_percentage()
            self.zoom_label.setText(f"{percentage}%")

    def _create_metadata_panel(self) -> QWidget:
        """Crear panel de metadatos"""
        panel = QFrame()
        panel.setObjectName("metadataPanel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("📋 Metadatos")
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        title.setFont(font)
        layout.addWidget(title)

        # Scroll area para metadatos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        metadata_widget = QWidget()
        self.metadata_layout = QVBoxLayout(metadata_widget)
        self.metadata_layout.setSpacing(12)
        self.metadata_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(metadata_widget)
        layout.addWidget(scroll, stretch=1)

        return panel

    def _create_actions_toolbar(self) -> QWidget:
        """Crear toolbar de acciones"""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(70)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Toggle favorito
        is_favorite = self.item_data.get('is_favorite', False)
        fav_icon = "⭐" if is_favorite else "☆"
        self.favorite_btn = QPushButton(f"{fav_icon} Favorito")
        self.favorite_btn.setCheckable(True)
        self.favorite_btn.setChecked(is_favorite)
        self.favorite_btn.clicked.connect(self._toggle_favorite)

        # Copiar imagen
        copy_img_btn = QPushButton("📋 Copiar Imagen")
        copy_img_btn.clicked.connect(self._copy_image_to_clipboard)

        # Copiar ruta
        copy_path_btn = QPushButton("📄 Copiar Ruta")
        copy_path_btn.clicked.connect(self._copy_path_to_clipboard)

        # Abrir en carpeta
        open_folder_btn = QPushButton("📂 Abrir Carpeta")
        open_folder_btn.clicked.connect(self._open_in_folder)

        # Editar (placeholder para FASE 6)
        edit_btn = QPushButton("✏️ Editar")
        edit_btn.clicked.connect(self._edit_metadata)

        # Eliminar
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(self._delete_item)

        layout.addWidget(self.favorite_btn)
        layout.addWidget(copy_img_btn)
        layout.addWidget(copy_path_btn)
        layout.addWidget(open_folder_btn)
        layout.addStretch()
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)

        return toolbar

    def load_image(self):
        """Cargar imagen en el viewer"""
        try:
            if not self.image_path or not os.path.exists(self.image_path):
                logger.error(f"Image not found: {self.image_path}")
                self._show_error("Imagen no encontrada")
                return

            # Cargar imagen
            pixmap = QPixmap(self.image_path)

            if pixmap.isNull():
                logger.error(f"Failed to load image: {self.image_path}")
                self._show_error("Error al cargar imagen")
                return

            # Establecer en viewer
            self.image_view.set_image(pixmap)

            logger.info(f"Image loaded: {pixmap.width()}x{pixmap.height()}")

        except Exception as e:
            logger.error(f"Error loading image: {e}", exc_info=True)
            self._show_error(f"Error al cargar imagen:\n{str(e)}")

    def load_metadata(self):
        """Cargar metadatos en el panel"""
        try:
            # Nombre
            self._add_metadata_row("Nombre:", self.item_data.get('label', 'N/A'))

            # Categoría
            category_icon = self.item_data.get('category_icon', '📁')
            category_name = self.item_data.get('category_name', 'Sin categoría')
            self._add_metadata_row("Categoría:", f"{category_icon} {category_name}")

            # Tags
            tags = self.item_data.get('tags', [])
            if tags:
                tags_text = ', '.join(tags)
                self._add_metadata_row("Tags:", f"🏷️ {tags_text}")

            # Descripción
            description = self.item_data.get('description', '')
            if description:
                self._add_metadata_row("Descripción:", description, multiline=True)

            # Separador
            self._add_separator()

            # Ruta
            self._add_metadata_row("Ruta:", self.image_path, copyable=True)

            # Información del archivo
            if os.path.exists(self.image_path):
                # Tamaño
                size_bytes = os.path.getsize(self.image_path)
                size_mb = size_bytes / (1024 * 1024)
                size_text = f"{size_mb:.2f} MB ({size_bytes:,} bytes)"
                self._add_metadata_row("Tamaño:", size_text)

                # Dimensiones (de la imagen cargada)
                if hasattr(self.image_view, 'pixmap_item') and self.image_view.pixmap_item:
                    pixmap = self.image_view.pixmap_item.pixmap()
                    dimensions = f"{pixmap.width()} x {pixmap.height()} px"
                    self._add_metadata_row("Dimensiones:", dimensions)

                # Formato
                ext = Path(self.image_path).suffix.upper()
                self._add_metadata_row("Formato:", ext.replace('.', ''))

                # Hash SHA-256 (opcional, puede ser lento para imágenes grandes)
                # self._add_metadata_row("Hash SHA-256:", self._calculate_file_hash())

                # Fechas
                created_timestamp = self.item_data.get('created_at')
                if created_timestamp:
                    try:
                        created_date = datetime.fromisoformat(created_timestamp)
                        self._add_metadata_row("Fecha creación:", created_date.strftime("%d/%m/%Y %H:%M"))
                    except:
                        pass

                # Última modificación del archivo
                mtime = os.path.getmtime(self.image_path)
                mtime_date = datetime.fromtimestamp(mtime)
                self._add_metadata_row("Modificado:", mtime_date.strftime("%d/%m/%Y %H:%M"))

            # Separador
            self._add_separator()

            # Favorito
            is_fav = self.item_data.get('is_favorite', False)
            fav_text = "Sí ⭐" if is_fav else "No"
            self._add_metadata_row("Favorito:", fav_text)

            # ID (útil para debugging)
            item_id = self.item_data.get('id')
            if item_id:
                self._add_metadata_row("ID:", str(item_id))

        except Exception as e:
            logger.error(f"Error loading metadata: {e}", exc_info=True)

    def _add_metadata_row(self, label: str, value: str, multiline: bool = False, copyable: bool = False):
        """Agregar fila de metadata"""
        container = QWidget()
        layout = QVBoxLayout(container) if multiline else QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("metadataLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        label_widget.setFont(font)

        # Value
        value_widget = QLabel(value)
        value_widget.setObjectName("metadataValue")
        value_widget.setWordWrap(True)
        value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if multiline:
            layout.addWidget(label_widget)
            layout.addWidget(value_widget)
        else:
            label_widget.setFixedWidth(120)
            layout.addWidget(label_widget)
            layout.addWidget(value_widget, stretch=1)

        self.metadata_layout.addWidget(container)

    def _add_separator(self):
        """Agregar separador en metadata"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        self.metadata_layout.addWidget(separator)

    def _calculate_file_hash(self) -> str:
        """Calcular hash SHA-256 del archivo"""
        try:
            sha256 = hashlib.sha256()
            with open(self.image_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()[:16] + "..."  # Primeros 16 chars
        except Exception as e:
            logger.error(f"Error calculating hash: {e}")
            return "N/A"

    # Métodos de acciones

    def _toggle_favorite(self):
        """Toggle estado de favorito"""
        item_id = self.item_data.get('id')
        is_favorite = self.favorite_btn.isChecked()

        try:
            # Actualizar en BD
            self.controller.db.update_item(item_id, is_favorite=is_favorite)

            # Actualizar item_data local
            self.item_data['is_favorite'] = is_favorite

            # Actualizar botón
            fav_icon = "⭐" if is_favorite else "☆"
            self.favorite_btn.setText(f"{fav_icon} Favorito")

            # Emitir señal
            self.favorite_toggled.emit(item_id, is_favorite)

            logger.info(f"Favorite toggled: {item_id} -> {is_favorite}")

        except Exception as e:
            logger.error(f"Error toggling favorite: {e}", exc_info=True)
            self._show_error(f"Error al actualizar favorito:\n{str(e)}")

    def _copy_image_to_clipboard(self):
        """Copiar imagen al portapapeles"""
        try:
            from PyQt6.QtWidgets import QApplication

            if hasattr(self.image_view, 'pixmap_item') and self.image_view.pixmap_item:
                pixmap = self.image_view.pixmap_item.pixmap()
                QApplication.clipboard().setPixmap(pixmap)

                QMessageBox.information(
                    self,
                    "Copiado",
                    "Imagen copiada al portapapeles"
                )
                logger.info("Image copied to clipboard")
            else:
                self._show_error("No hay imagen cargada")

        except Exception as e:
            logger.error(f"Error copying image: {e}", exc_info=True)
            self._show_error(f"Error al copiar imagen:\n{str(e)}")

    def _copy_path_to_clipboard(self):
        """Copiar ruta al portapapeles"""
        try:
            import pyperclip
            pyperclip.copy(self.image_path)

            QMessageBox.information(
                self,
                "Copiado",
                f"Ruta copiada al portapapeles:\n\n{self.image_path}"
            )
            logger.info(f"Path copied: {self.image_path}")

        except Exception as e:
            logger.error(f"Error copying path: {e}", exc_info=True)
            self._show_error(f"Error al copiar ruta:\n{str(e)}")

    def _open_in_folder(self):
        """Abrir explorador en la carpeta del archivo"""
        try:
            if os.path.exists(self.image_path):
                # Windows: usar explorer con /select
                if os.name == 'nt':
                    subprocess.run(['explorer', '/select,', self.image_path])
                # Linux: xdg-open en el directorio
                elif os.name == 'posix':
                    directory = os.path.dirname(self.image_path)
                    subprocess.run(['xdg-open', directory])
                # Mac: open -R
                else:
                    subprocess.run(['open', '-R', self.image_path])

                logger.info(f"Opened folder: {self.image_path}")
            else:
                self._show_error("El archivo no existe")

        except Exception as e:
            logger.error(f"Error opening folder: {e}", exc_info=True)
            self._show_error(f"Error al abrir carpeta:\n{str(e)}")

    def _edit_metadata(self):
        """Editar metadatos (FASE 6)"""
        try:
            from src.views.image_gallery.edit_metadata_dialog import EditMetadataDialog

            # Obtener categorías disponibles
            categories = self.controller.get_categories_with_images()

            # Crear diálogo de edición
            edit_dialog = EditMetadataDialog(
                item_data=self.item_data,
                categories=categories,
                parent=self
            )

            # Conectar señal
            edit_dialog.metadata_updated.connect(self._on_metadata_updated)

            # Mostrar diálogo
            edit_dialog.exec()

        except Exception as e:
            logger.error(f"Error opening edit dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al abrir editor:\n{str(e)}"
            )

    def _on_metadata_updated(self, item_id: int, updated_data: dict):
        """
        Handler cuando se actualizan metadatos

        Args:
            item_id: ID del item
            updated_data: Datos actualizados
        """
        try:
            logger.info(f"Updating metadata for item {item_id}: {updated_data}")

            # Actualizar en BD
            self.controller.db.update_item(item_id, **updated_data)

            # Actualizar item_data local
            for key, value in updated_data.items():
                self.item_data[key] = value

            # Recargar metadatos en el panel
            # Limpiar layout actual
            while self.metadata_layout.count():
                item = self.metadata_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Recargar
            self.load_metadata()

            # Actualizar título si cambió el nombre
            if 'label' in updated_data:
                self.setWindowTitle(f"Preview - {updated_data['label']}")

            # Emitir señal para que la ventana principal recargue
            self.item_updated.emit(item_id)

            QMessageBox.information(
                self,
                "Actualizado",
                "Metadatos actualizados exitosamente"
            )

            logger.info(f"Metadata updated successfully for item {item_id}")

        except Exception as e:
            logger.error(f"Error updating metadata: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al actualizar metadatos:\n{str(e)}"
            )

    def _delete_item(self):
        """Eliminar item con confirmación"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar esta imagen?\n\n{self.item_data.get('label')}\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                item_id = self.item_data.get('id')

                # Eliminar desde BD
                self.controller.db.delete_item(item_id)

                # Emitir señal
                self.item_deleted.emit(item_id)

                logger.info(f"Item deleted: {item_id}")

                # Cerrar diálogo
                QMessageBox.information(
                    self,
                    "Eliminado",
                    "Imagen eliminada exitosamente"
                )

                self.close()

            except Exception as e:
                logger.error(f"Error deleting item: {e}", exc_info=True)
                self._show_error(f"Error al eliminar:\n{str(e)}")

    def _show_error(self, message: str):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", message)

    def _get_stylesheet(self) -> str:
        """Obtener stylesheet"""
        return """
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            #header {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
            #viewerContainer {
                background-color: #1a1a1a;
            }
            #zoomControls {
                background-color: #2d2d2d;
                border-radius: 6px;
            }
            #metadataPanel {
                background-color: #252525;
                border-left: 1px solid #3d3d3d;
            }
            #toolbar {
                background-color: #2d2d2d;
                border-top: 1px solid #3d3d3d;
            }
            QLabel {
                color: #e0e0e0;
            }
            #metadataLabel {
                color: #888888;
                font-size: 9pt;
            }
            #metadataValue {
                color: #e0e0e0;
                font-size: 9pt;
            }
            #separator {
                background-color: #3d3d3d;
                max-height: 1px;
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
            QPushButton:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
            }
            QPushButton#closeButton {
                background-color: transparent;
                border: none;
                font-size: 16pt;
            }
            QPushButton#closeButton:hover {
                background-color: #d32f2f;
            }
            QPushButton#deleteButton {
                background-color: #d32f2f;
                border: 1px solid #d32f2f;
            }
            QPushButton#deleteButton:hover {
                background-color: #e53935;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
        """
