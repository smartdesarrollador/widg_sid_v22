"""
AI Bulk Config Step - Paso 1: Configuración de opciones para bulk import

Este step permite configurar:
- Categoría destino
- Tags por defecto
- Tipo de items
- Opciones (favoritos, sensibles)
- Contexto del usuario
"""
import sys
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QTextEdit, QCheckBox,
    QFormLayout, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Agregar path al sys.path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import DBManager
from models.bulk_item_data import BulkItemDefaults, BulkImportConfig
from views.widgets.tag_group_selector import TagGroupSelector

logger = logging.getLogger(__name__)


class ConfigStep(QWidget):
    """
    Step 1: Configuración de opciones para bulk import.

    Permite seleccionar:
    - Categoría destino
    - Tags (con autocompletar desde tag_groups)
    - Tipo de item (TEXT, URL, CODE, PATH)
    - Is favorite (checkbox)
    - Is sensitive (checkbox)
    - Contexto del usuario (qué necesita)
    """

    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.categories = []

        self.init_ui()
        self.load_categories()

    def init_ui(self):
        """Inicializa la interfaz del step."""
        # Scroll area para todo el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #252525;
            }
        """)

        # Widget contenedor
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #252525;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Título del step
        title = QLabel("⚙️ Configuración de Importación")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #00d4ff; padding: 10px;")
        layout.addWidget(title)

        # Descripción
        desc = QLabel(
            "Configura las opciones por defecto que se aplicarán a los items "
            "que genere la IA. Estos valores se pueden sobreescribir individualmente "
            "en cada item."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888888; padding: 0 10px 10px 10px;")
        layout.addWidget(desc)

        # === Grupo: Destino ===
        dest_group = QGroupBox("Destino")
        dest_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                color: #00d4ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        dest_layout = QFormLayout()
        dest_layout.setSpacing(10)
        dest_layout.setContentsMargins(15, 15, 15, 15)

        # Categoría (requerido)
        category_label = QLabel("Categoría: *")
        category_label.setStyleSheet("color: #ffffff; font-weight: normal;")
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 11pt;
            }
            QComboBox:hover {
                border-color: #00d4ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #00d4ff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: #ffffff;
                selection-background-color: #00d4ff;
                selection-color: #000000;
                border: 1px solid #3d3d3d;
            }
        """)
        dest_layout.addRow(category_label, self.category_combo)

        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)

        # === Grupo: Valores por Defecto ===
        defaults_group = QGroupBox("Valores por Defecto")
        defaults_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                color: #00d4ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        defaults_layout = QFormLayout()
        defaults_layout.setSpacing(10)
        defaults_layout.setContentsMargins(15, 15, 15, 15)

        # Tipo de item
        type_label = QLabel("Tipo de Item:")
        type_label.setStyleSheet("color: #ffffff; font-weight: normal;")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['CODE', 'URL', 'TEXT', 'PATH'])
        self.type_combo.setCurrentText('CODE')  # Default: CODE
        self.type_combo.setStyleSheet(self.category_combo.styleSheet())
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        defaults_layout.addRow(type_label, self.type_combo)

        # Tags con TagGroupSelector
        tags_label = QLabel("Tags:")
        tags_label.setStyleSheet("color: #ffffff; font-weight: normal;")

        # Usar TagGroupSelector si está disponible
        try:
            db_path = str(Path(self.db.db_path))
            self.tags_selector = TagGroupSelector(db_path=db_path)
            self.tags_selector.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                }
            """)
            defaults_layout.addRow(tags_label, self.tags_selector)
        except Exception as e:
            logger.warning(f"TagGroupSelector not available, using QLineEdit: {e}")
            self.tags_selector = QLineEdit()
            self.tags_selector.setPlaceholderText("Ej: git, deploy, python")
            self.tags_selector.setStyleSheet("""
                QLineEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    padding: 8px;
                    font-size: 11pt;
                }
                QLineEdit:hover {
                    border-color: #00d4ff;
                }
                QLineEdit:focus {
                    border-color: #00d4ff;
                }
            """)
            defaults_layout.addRow(tags_label, self.tags_selector)

        # Checkboxes (favorito, sensible, lista)
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(8)

        self.is_favorite_check = QCheckBox("Marcar como favoritos")
        self.is_favorite_check.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 11pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:hover {
                border-color: #00d4ff;
            }
            QCheckBox::indicator:checked {
                background-color: #00d4ff;
                border-color: #00d4ff;
                image: none;
            }
        """)
        checkbox_layout.addWidget(self.is_favorite_check)

        self.is_sensitive_check = QCheckBox("Marcar como sensibles (encriptar)")
        self.is_sensitive_check.setStyleSheet(self.is_favorite_check.styleSheet())
        checkbox_layout.addWidget(self.is_sensitive_check)

        self.is_list_check = QCheckBox("Crear como lista secuencial")
        self.is_list_check.setStyleSheet(self.is_favorite_check.styleSheet())
        self.is_list_check.stateChanged.connect(self.on_list_check_changed)
        checkbox_layout.addWidget(self.is_list_check)

        defaults_layout.addRow("Opciones:", checkbox_layout)

        # Nombre de lista (oculto inicialmente)
        list_name_label = QLabel("Nombre de lista:")
        list_name_label.setStyleSheet("color: #ffffff; font-weight: normal;")
        self.list_name_input = QLineEdit()
        self.list_name_input.setPlaceholderText("Ej: Pasos para deploy, Setup inicial...")
        self.list_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 11pt;
            }
            QLineEdit:hover {
                border-color: #00d4ff;
            }
            QLineEdit:focus {
                border-color: #00d4ff;
            }
        """)
        self.list_name_input.setVisible(False)
        list_name_label.setVisible(False)
        self.list_name_label = list_name_label  # Guardar referencia
        defaults_layout.addRow(list_name_label, self.list_name_input)

        defaults_group.setLayout(defaults_layout)
        layout.addWidget(defaults_group)

        # === Grupo: Contexto del Usuario ===
        context_group = QGroupBox("Contexto de la Tarea")
        context_group.setStyleSheet(defaults_group.styleSheet())
        context_layout = QVBoxLayout()
        context_layout.setSpacing(10)
        context_layout.setContentsMargins(15, 15, 15, 15)

        context_desc = QLabel(
            "Describe qué necesitas que genere la IA. Ejemplo:\n"
            "• Pasos para clonar un repositorio e instalar dependencias\n"
            "• Comandos para deploy a VPS con Docker\n"
            "• URLs de documentación de React y Next.js"
        )
        context_desc.setWordWrap(True)
        context_desc.setStyleSheet("color: #888888; font-size: 10pt; padding-bottom: 5px;")
        context_layout.addWidget(context_desc)

        self.context_text = QTextEdit()
        self.context_text.setPlaceholderText("Describe lo que necesitas...")
        self.context_text.setMinimumHeight(120)
        self.context_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 11pt;
                font-family: Consolas, monospace;
            }
            QTextEdit:hover {
                border-color: #00d4ff;
            }
            QTextEdit:focus {
                border-color: #00d4ff;
            }
        """)
        context_layout.addWidget(self.context_text)

        context_group.setLayout(context_layout)
        layout.addWidget(context_group)

        # Tips según tipo
        self.tips_label = QLabel()
        self.tips_label.setWordWrap(True)
        self.tips_label.setStyleSheet("""
            QLabel {
                background-color: #1e3a4d;
                color: #ffffff;
                border-left: 4px solid #00d4ff;
                border-radius: 3px;
                padding: 12px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.tips_label)
        self.update_tips()

        layout.addStretch()

        # Nota de campo requerido
        required_note = QLabel("* Campos requeridos")
        required_note.setStyleSheet("color: #888888; font-size: 9pt; font-style: italic;")
        layout.addWidget(required_note)

        scroll.setWidget(container)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def load_categories(self):
        """Carga categorías desde BD."""
        try:
            query = "SELECT id, name, icon FROM categories WHERE is_active = 1 ORDER BY order_index"
            result = self.db.execute_query(query)

            self.categories = []
            self.category_combo.clear()

            for row in result:
                cat_id = row['id']
                cat_name = row['name']
                cat_icon = row.get('icon', '')

                display_text = f"{cat_icon} {cat_name}" if cat_icon else cat_name

                self.category_combo.addItem(display_text, cat_id)
                self.categories.append({'id': cat_id, 'name': cat_name, 'icon': cat_icon})

            logger.debug(f"Loaded {len(self.categories)} categories")

        except Exception as e:
            logger.error(f"Error loading categories: {e}")

    def on_type_changed(self, item_type: str):
        """Actualiza tips cuando cambia el tipo."""
        self.update_tips()

    def on_list_check_changed(self, state):
        """Muestra/oculta el campo de nombre de lista según el checkbox."""
        is_checked = bool(state)
        self.list_name_input.setVisible(is_checked)
        self.list_name_label.setVisible(is_checked)

    def update_tips(self):
        """Actualiza tips según el tipo seleccionado."""
        item_type = self.type_combo.currentText()

        tips = {
            'CODE': "💡 <b>Tips para CODE:</b><br>"
                   "• Comandos de terminal listos para ejecutar<br>"
                   "• Scripts multilínea<br>"
                   "• Ejemplo: git clone, npm install, docker run",

            'URL': "💡 <b>Tips para URL:</b><br>"
                   "• URLs completas (https://...)<br>"
                   "• Documentación, dashboards, recursos<br>"
                   "• Ejemplo: docs oficiales, repos GitHub",

            'TEXT': "💡 <b>Tips para TEXT:</b><br>"
                    "• Notas, recordatorios, instrucciones<br>"
                    "• Puede ser multilínea<br>"
                    "• Ejemplo: procedimientos, contactos",

            'PATH': "💡 <b>Tips para PATH:</b><br>"
                    "• Rutas absolutas o relativas<br>"
                    "• Archivos o directorios<br>"
                    "• Ejemplo: /etc/nginx/nginx.conf, ~/.bashrc"
        }

        self.tips_label.setText(tips.get(item_type, ""))

    def get_config(self) -> BulkImportConfig:
        """
        Obtiene la configuración actual del step.

        Returns:
            BulkImportConfig con la configuración
        """
        # Obtener categoría seleccionada
        category_id = self.category_combo.currentData()
        category_name = self.categories[self.category_combo.currentIndex()]['name'] if self.categories else "Unknown"

        # Obtener tags
        if hasattr(self.tags_selector, 'get_selected_tags'):
            # TagGroupSelector
            tags = ', '.join(self.tags_selector.get_selected_tags())
        else:
            # QLineEdit
            tags = self.tags_selector.text().strip()

        # Crear defaults
        defaults = BulkItemDefaults(
            type=self.type_combo.currentText(),
            tags=tags,
            is_favorite=1 if self.is_favorite_check.isChecked() else 0,
            is_sensitive=1 if self.is_sensitive_check.isChecked() else 0,
            is_list=1 if self.is_list_check.isChecked() else 0,
            list_group=self.list_name_input.text().strip() if self.is_list_check.isChecked() else None
        )

        # Crear config
        config = BulkImportConfig(
            category_id=category_id,
            category_name=category_name,
            defaults=defaults,
            user_context=self.context_text.toPlainText().strip()
        )

        return config

    def is_valid(self) -> bool:
        """
        Valida que el step tiene los datos mínimos requeridos.

        Returns:
            True si es válido, False si no
        """
        # Categoría requerida
        if self.category_combo.currentIndex() < 0:
            return False

        return True

    def set_config(self, config: BulkImportConfig):
        """
        Establece configuración en el step (útil para cargar config guardada).

        Args:
            config: Configuración a cargar
        """
        # Buscar y seleccionar categoría
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == config.category_id:
                self.category_combo.setCurrentIndex(i)
                break

        # Tipo
        self.type_combo.setCurrentText(config.defaults.type)

        # Tags
        if hasattr(self.tags_selector, 'set_tags'):
            tags_list = [t.strip() for t in config.defaults.tags.split(',') if t.strip()]
            self.tags_selector.set_tags(tags_list)
        else:
            self.tags_selector.setText(config.defaults.tags)

        # Checkboxes
        self.is_favorite_check.setChecked(config.defaults.is_favorite == 1)
        self.is_sensitive_check.setChecked(config.defaults.is_sensitive == 1)

        # Lista
        if hasattr(config.defaults, 'is_list'):
            self.is_list_check.setChecked(config.defaults.is_list == 1)
            if config.defaults.is_list == 1 and hasattr(config.defaults, 'list_group'):
                self.list_name_input.setText(config.defaults.list_group or "")

        # Contexto
        self.context_text.setPlainText(config.user_context)
