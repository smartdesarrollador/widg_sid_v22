"""
Table Config Step - Paso 1: Configuración de tabla

Este step permite configurar:
- Nombre de tabla (único)
- Número de filas (1-100)
- Número de columnas (1-20)
- Nombres de columnas
- Categoría destino
- Tags opcionales
"""
import sys
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QSpinBox,
    QFormLayout, QGroupBox, QScrollArea, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Agregar path al sys.path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import DBManager
from core.table_validator import TableValidator

logger = logging.getLogger(__name__)


class TableConfigStep(QWidget):
    """
    Step 1: Configuración de tabla.

    Permite definir:
    - Nombre de tabla
    - Dimensiones (filas × columnas)
    - Nombres de columnas
    - Categoría destino
    - Tags opcionales
    """

    def __init__(self, db_manager: DBManager, controller=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.controller = controller
        self.categories = []

        # Widgets de columnas (dinámico)
        self.column_inputs = []
        self.column_sensitive_checks = []  # Checkboxes para marcar columnas sensibles
        self.column_url_checks = []  # Checkboxes para marcar columnas como tipo URL

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
        title = QLabel("📊 Configuración de Tabla")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #00d4ff; padding: 10px;")
        layout.addWidget(title)

        # Descripción
        desc = QLabel(
            "Define el nombre, dimensiones y estructura de tu tabla de items.\n"
            "Los datos se ingresarán en el siguiente paso."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaaaaa; font-size: 10pt; padding: 0 10px 10px 10px;")
        layout.addWidget(desc)

        # Grupo: Información Básica
        basic_group = QGroupBox("Información Básica")
        basic_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
                background-color: #2b2b2b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        basic_layout = QFormLayout()
        basic_layout.setSpacing(12)

        # Nombre de tabla
        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("Ej: DATOS_PERSONALES")
        self.table_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        basic_layout.addRow("Nombre de tabla:", self.table_name_input)

        # Categoría
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
            }
            QComboBox:focus {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #cccccc;
                selection-background-color: #007acc;
            }
        """)
        basic_layout.addRow("Categoría:", self.category_combo)

        # Tags (opcional)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Ej: trabajo, contactos (separados por comas)")
        self.tags_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        basic_layout.addRow("Tags (opcional):", self.tags_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Grupo: Dimensiones
        dims_group = QGroupBox("Dimensiones de Tabla")
        dims_group.setStyleSheet(basic_group.styleSheet())
        dims_layout = QFormLayout()
        dims_layout.setSpacing(12)

        # Filas
        filas_layout = QHBoxLayout()
        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setMinimum(1)
        self.rows_spinbox.setMaximum(100)
        self.rows_spinbox.setValue(5)
        self.rows_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
            }
            QSpinBox:focus {
                border: 1px solid #007acc;
            }
        """)
        filas_layout.addWidget(self.rows_spinbox)
        filas_layout.addWidget(QLabel("(máximo 100)"))
        filas_layout.addStretch()
        dims_layout.addRow("Número de filas:", filas_layout)

        # Columnas
        cols_layout = QHBoxLayout()
        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setMinimum(1)
        self.cols_spinbox.setMaximum(20)
        self.cols_spinbox.setValue(3)
        self.cols_spinbox.setStyleSheet(self.rows_spinbox.styleSheet())
        self.cols_spinbox.valueChanged.connect(self.update_column_inputs)
        cols_layout.addWidget(self.cols_spinbox)
        cols_layout.addWidget(QLabel("(máximo 20)"))
        cols_layout.addStretch()
        dims_layout.addRow("Número de columnas:", cols_layout)

        dims_group.setLayout(dims_layout)
        layout.addWidget(dims_group)

        # Grupo: Nombres de Columnas
        self.columns_group = QGroupBox("Nombres de Columnas")
        self.columns_group.setStyleSheet(basic_group.styleSheet())
        self.columns_layout = QVBoxLayout()
        self.columns_layout.setSpacing(8)

        self.columns_group.setLayout(self.columns_layout)
        layout.addWidget(self.columns_group)

        # Inicializar inputs de columnas
        self.update_column_inputs(self.cols_spinbox.value())

        layout.addStretch()

        scroll.setWidget(container)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def update_column_inputs(self, num_cols):
        """Actualiza los inputs de nombres de columnas dinámicamente."""
        # Limpiar inputs existentes
        while self.columns_layout.count():
            item = self.columns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.column_inputs = []
        self.column_sensitive_checks = []
        self.column_url_checks = []

        # Crear nuevos inputs
        for i in range(num_cols):
            col_layout = QHBoxLayout()

            label = QLabel(f"Columna {i+1}:")
            label.setMinimumWidth(80)
            col_layout.addWidget(label)

            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Ej: NOMBRE, EMAIL, TELEFONO")
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #1e1e1e;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 6px;
                    color: #cccccc;
                }
                QLineEdit:focus {
                    border: 1px solid #007acc;
                }
            """)
            col_layout.addWidget(input_field, 1)

            # Checkbox para marcar como tipo URL
            url_check = QCheckBox("🔗 URL")
            url_check.setToolTip("Marcar si esta columna contiene URLs")
            url_check.setStyleSheet("""
                QCheckBox {
                    color: #cccccc;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 1px solid #4CAF50;
                }
                QCheckBox::indicator:hover {
                    border: 1px solid #4CAF50;
                }
            """)
            col_layout.addWidget(url_check)

            # Checkbox para marcar como sensible
            sensitive_check = QCheckBox("🔒 Sensible")
            sensitive_check.setToolTip("Marcar si esta columna contiene datos sensibles (contraseñas, claves, etc.)")
            sensitive_check.setStyleSheet("""
                QCheckBox {
                    color: #cccccc;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background-color: #007acc;
                    border: 1px solid #007acc;
                }
                QCheckBox::indicator:hover {
                    border: 1px solid #007acc;
                }
            """)
            col_layout.addWidget(sensitive_check)

            self.columns_layout.addLayout(col_layout)
            self.column_inputs.append(input_field)
            self.column_url_checks.append(url_check)
            self.column_sensitive_checks.append(sensitive_check)

    def load_categories(self):
        """Carga las categorías en el combo."""
        try:
            if self.controller:
                self.categories = self.controller.categories
            else:
                cats = self.db.get_categories()
                # Convertir dicts a objetos con atributos
                from models.category import Category
                self.categories = []
                for cat_dict in cats:
                    cat = Category(
                        id=cat_dict.get('id'),
                        name=cat_dict.get('name'),
                        icon=cat_dict.get('icon', '📁')
                    )
                    self.categories.append(cat)

            self.category_combo.clear()
            for category in self.categories:
                self.category_combo.addItem(
                    f"{category.icon} {category.name}",
                    category.id
                )

            logger.info(f"Loaded {len(self.categories)} categories")

        except Exception as e:
            logger.error(f"Error loading categories: {e}")

    def is_valid(self) -> bool:
        """Valida que el step tenga datos válidos."""
        # Validar nombre de tabla
        table_name = self.table_name_input.text().strip()
        if not table_name:
            return False

        # Validar que tenga al menos un nombre de columna
        col_names = [inp.text().strip() for inp in self.column_inputs if inp.text().strip()]
        if not col_names:
            return False

        # Validar categoría seleccionada
        if self.category_combo.currentIndex() < 0:
            return False

        return True

    def get_config(self) -> dict:
        """Retorna la configuración del step."""
        # Obtener nombres de columnas
        column_names = []
        for i, inp in enumerate(self.column_inputs):
            name = inp.text().strip()
            if name:
                column_names.append(name)
            else:
                column_names.append(f"COL_{i+1}")

        # Obtener estado de columnas sensibles
        sensitive_columns = []
        for i, checkbox in enumerate(self.column_sensitive_checks):
            if checkbox.isChecked():
                sensitive_columns.append(i)  # Índice de columna sensible

        # Obtener estado de columnas URL
        url_columns = []
        for i, checkbox in enumerate(self.column_url_checks):
            if checkbox.isChecked():
                url_columns.append(i)  # Índice de columna URL

        # Procesar tags
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []

        return {
            'table_name': self.table_name_input.text().strip(),
            'rows': self.rows_spinbox.value(),
            'cols': self.cols_spinbox.value(),
            'column_names': column_names,
            'sensitive_columns': sensitive_columns,  # Lista de índices de columnas sensibles
            'url_columns': url_columns,  # Lista de índices de columnas URL
            'category_id': self.category_combo.currentData(),
            'tags': tags
        }
