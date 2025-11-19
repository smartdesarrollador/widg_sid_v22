"""
Item Details Dialog - Muestra información detallada de un item
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QWidget, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.item import Item
from database.db_manager import DBManager
import logging

logger = logging.getLogger(__name__)


class ItemDetailsDialog(QDialog):
    """Diálogo que muestra información detallada de un item"""

    def __init__(self, item: Item, floating_panel=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.floating_panel = floating_panel  # Optional reference to FloatingPanel for refresh
        self.db = DBManager()
        self.category_name = self.get_category_name()
        self.init_ui()

    def get_category_name(self) -> str:
        """Obtener el nombre de la categoría del item"""
        try:
            # Buscar la categoría a la que pertenece este item
            categories = self.db.get_categories()  # Fixed: was get_all_categories()
            for category in categories:
                items = self.db.get_items_by_category(category['id'])
                for item in items:
                    if item.get('id') == self.item.id:
                        return category['name']
            return "Desconocida"
        except Exception as e:
            logger.error(f"Error getting category name: {e}")
            return "Desconocida"

    def init_ui(self):
        """Inicializar UI"""
        self.setWindowTitle("ℹ️ Detalles del Item")
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header con icono y label
        header_layout = QHBoxLayout()
        header_icon = QLabel("ℹ️")
        header_icon.setStyleSheet("font-size: 32pt;")
        header_layout.addWidget(header_icon)

        header_label = QLabel(self.item.label)
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setWordWrap(True)
        header_layout.addWidget(header_label, 1)

        main_layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Scroll area para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor del scroll
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # Información básica
        basic_group = self.create_group("📋 Información Básica", [
            ("Categoría", f"📁 {self.category_name}"),
            ("Label", self.item.label),
            ("Tipo", self.get_type_display()),
            ("ID", str(self.item.id))
        ])
        content_layout.addWidget(basic_group)

        # Contenido
        content_group = self.create_content_group()
        content_layout.addWidget(content_group)

        # Tags
        if self.item.tags and len(self.item.tags) > 0:
            tags_group = self.create_tags_group()
            content_layout.addWidget(tags_group)

        # Descripción
        if hasattr(self.item, 'description') and self.item.description:
            description_group = self.create_description_group()
            content_layout.addWidget(description_group)

        # Propiedades adicionales
        additional_props = self.get_additional_properties()
        if additional_props:
            additional_group = self.create_group("⚙️ Propiedades Adicionales", additional_props)
            content_layout.addWidget(additional_group)

        # Estadísticas
        stats_group = self.create_stats_group()
        content_layout.addWidget(stats_group)

        # Flags/Estado
        flags_group = self.create_flags_group()
        content_layout.addWidget(flags_group)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)

        # Estilos
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #cccccc;
            }
            QLabel {
                color: #cccccc;
                background-color: transparent;
            }
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #f093fb;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #2d2d2d;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QScrollArea {
                border: none;
            }
        """)

    def create_group(self, title: str, items: list) -> QGroupBox:
        """Crear un grupo con título y lista de items (label, value)"""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        for label, value in items:
            item_layout = QHBoxLayout()

            label_widget = QLabel(f"{label}:")
            label_widget.setMinimumWidth(150)
            label_font = QFont()
            label_font.setBold(True)
            label_widget.setFont(label_font)
            label_widget.setStyleSheet("color: #999999;")
            item_layout.addWidget(label_widget)

            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_widget.setStyleSheet("color: #ffffff;")
            item_layout.addWidget(value_widget, 1)

            layout.addLayout(item_layout)

        group.setLayout(layout)
        return group

    def create_content_group(self) -> QGroupBox:
        """Crear grupo de contenido"""
        group = QGroupBox("📄 Contenido")
        layout = QVBoxLayout()

        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive:
            # Contenido sensible - ofuscado
            content_label = QLabel("🔒 Contenido Sensible (oculto por seguridad)")
            content_label.setStyleSheet("""
                color: #cc0000;
                background-color: #3d2020;
                padding: 10px;
                border-radius: 4px;
                font-style: italic;
            """)
        else:
            # Contenido normal
            content_text = self.item.content if self.item.content else "(Vacío)"
            content_label = QLabel(content_text)
            content_label.setWordWrap(True)
            content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content_label.setStyleSheet("""
                color: #ffffff;
                background-color: #1e1e1e;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
            """)
            # Limitar altura máxima
            content_label.setMaximumHeight(200)

        layout.addWidget(content_label)
        group.setLayout(layout)
        return group

    def create_tags_group(self) -> QGroupBox:
        """Crear grupo de tags"""
        group = QGroupBox("🏷️ Tags")
        layout = QHBoxLayout()
        layout.setSpacing(5)

        for tag in self.item.tags:
            tag_label = QLabel(tag)
            tag_label.setStyleSheet("""
                background-color: #007acc;
                color: #ffffff;
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 9pt;
            """)
            layout.addWidget(tag_label)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_description_group(self) -> QGroupBox:
        """Crear grupo de descripción"""
        group = QGroupBox("📝 Descripción")
        layout = QVBoxLayout()

        description_label = QLabel(self.item.description)
        description_label.setWordWrap(True)
        description_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        description_label.setStyleSheet("""
            color: #ffffff;
            background-color: #1e1e1e;
            padding: 10px;
            border-radius: 4px;
        """)

        layout.addWidget(description_label)
        group.setLayout(layout)
        return group

    def get_additional_properties(self) -> list:
        """Obtener propiedades adicionales del item"""
        props = []

        if hasattr(self.item, 'working_dir') and self.item.working_dir:
            props.append(("Directorio de trabajo", self.item.working_dir))

        if hasattr(self.item, 'color') and self.item.color:
            color_display = f"{self.item.color} ■"
            props.append(("Color", color_display))

        if hasattr(self.item, 'list_group') and self.item.list_group:
            props.append(("Grupo de lista", self.item.list_group))
            props.append(("Orden en lista", str(self.item.orden_lista)))

        return props

    def create_stats_group(self) -> QGroupBox:
        """Crear grupo de estadísticas"""
        stats_items = []

        # Use count
        use_count = getattr(self.item, 'use_count', 0)
        stats_items.append(("Usos totales", f"{use_count} veces"))

        # Last used
        last_used = getattr(self.item, 'last_used', None)
        if last_used:
            try:
                if isinstance(last_used, datetime):
                    last_used_str = last_used.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_used_str = str(last_used)
                stats_items.append(("Último uso", last_used_str))
            except:
                stats_items.append(("Último uso", "Desconocido"))
        else:
            stats_items.append(("Último uso", "Nunca"))

        # Created at
        created_at = getattr(self.item, 'created_at', None)
        if created_at:
            try:
                if isinstance(created_at, datetime):
                    created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_str = str(created_at)
                stats_items.append(("Fecha de creación", created_str))
            except:
                pass

        return self.create_group("📊 Estadísticas de Uso", stats_items)

    def create_flags_group(self) -> QGroupBox:
        """Crear grupo de flags/estado con checkboxes editables"""
        group = QGroupBox("🚩 Estado")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Marcar como favorito checkbox (editable)
        favorite_layout = QHBoxLayout()
        self.favorite_checkbox = QCheckBox("⭐ Marcar como favorito")
        self.favorite_checkbox.setChecked(self.item.is_favorite)
        self.favorite_checkbox.stateChanged.connect(self.on_favorite_changed)
        self.favorite_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        favorite_layout.addWidget(self.favorite_checkbox)
        favorite_layout.addStretch()
        layout.addLayout(favorite_layout)

        # Marcar como archivado checkbox (editable)
        archived_layout = QHBoxLayout()
        self.archived_checkbox = QCheckBox("📦 Marcar como archivado")
        self.archived_checkbox.setChecked(self.item.is_archived)
        self.archived_checkbox.stateChanged.connect(self.on_archived_changed)
        self.archived_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        archived_layout.addWidget(self.archived_checkbox)
        archived_layout.addStretch()
        layout.addLayout(archived_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3d3d3d;")
        layout.addWidget(separator)

        # Read-only flags
        readonly_flags = [
            ("Es sensible", "✅ Sí" if self.item.is_sensitive else "❌ No"),
            ("Está activo", "✅ Sí" if self.item.is_active else "❌ No"),
        ]

        if hasattr(self.item, 'is_list'):
            readonly_flags.append(("Es parte de lista", "✅ Sí" if self.item.is_list else "❌ No"))

        for label, value in readonly_flags:
            flag_layout = QHBoxLayout()

            label_widget = QLabel(f"{label}:")
            label_widget.setMinimumWidth(150)
            label_font = QFont()
            label_font.setBold(True)
            label_widget.setFont(label_font)
            label_widget.setStyleSheet("color: #999999;")
            flag_layout.addWidget(label_widget)

            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: #ffffff;")
            flag_layout.addWidget(value_widget, 1)

            layout.addLayout(flag_layout)

        group.setLayout(layout)
        return group

    def on_favorite_changed(self, state):
        """Handle favorite checkbox state change"""
        try:
            is_favorite = bool(state)
            self.db.update_item(
                self.item.id,
                is_favorite=is_favorite
            )
            self.item.is_favorite = is_favorite
            logger.info(f"Item '{self.item.label}' favorite status changed to {is_favorite}")

            # Notify FloatingPanel directly if available
            if self.floating_panel and hasattr(self.floating_panel, 'on_item_state_changed'):
                self.floating_panel.on_item_state_changed(str(self.item.id))
        except Exception as e:
            logger.error(f"Error updating favorite status: {e}")

    def on_archived_changed(self, state):
        """Handle archived checkbox state change"""
        try:
            is_archived = bool(state)
            self.db.update_item(
                self.item.id,
                is_archived=is_archived
            )
            self.item.is_archived = is_archived
            logger.info(f"Item '{self.item.label}' archived status changed to {is_archived}")

            # Notify FloatingPanel directly if available
            if self.floating_panel and hasattr(self.floating_panel, 'on_item_state_changed'):
                self.floating_panel.on_item_state_changed(str(self.item.id))
        except Exception as e:
            logger.error(f"Error updating archived status: {e}")

    def get_type_display(self) -> str:
        """Obtener representación visual del tipo de item"""
        type_map = {
            'text': '📝 Texto',
            'url': '🌐 URL',
            'code': '⚡ Código/Comando',
            'path': '📁 Ruta/Archivo'
        }
        return type_map.get(self.item.type.value, self.item.type.value.upper())
