"""
AI Table Config Step - Paso 1: Configuración de prompt

Este step permite configurar:
- Nombre de tabla (único)
- Categoría destino
- Contexto del usuario (prompt para IA)
- Número de filas y columnas
- Definición manual de columnas (nombre, tipo URL, sensible)
- Tags opcionales
"""
import sys
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QSpinBox, QTextEdit,
    QFormLayout, QGroupBox, QScrollArea, QCheckBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Agregar path al sys.path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import DBManager
from models.ai_table_data import AITablePromptConfig

logger = logging.getLogger(__name__)


class AITableConfigStep(QWidget):
    """
    Step 1: Configuración de prompt para IA.

    Permite definir:
    - Nombre de tabla
    - Categoría destino
    - Contexto del usuario
    - Filas y columnas esperadas
    - Configuración manual de columnas
    - Tags opcionales
    """

    def __init__(self, db_manager: DBManager, controller=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.controller = controller
        self.categories = []
        self.column_configs = []  # Lista de configuraciones de columnas

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
        title = QLabel("🤖 Configuración de Prompt")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #00d4ff; padding: 10px;")
        layout.addWidget(title)

        # Descripción
        desc = QLabel(
            "Configura el prompt que se generará para ChatGPT, Claude u otra IA.\n"
            "Define la estructura de tu tabla y la IA generará los datos."
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
                color: #00d4ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        basic_layout = QFormLayout()
        basic_layout.setSpacing(15)

        # Nombre de tabla
        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("Ej: Python_Libraries_2025")
        self.table_name_input.setStyleSheet(self._get_input_style())
        basic_layout.addRow("Nombre de Tabla:", self.table_name_input)

        # Categoría
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(self._get_combo_style())
        basic_layout.addRow("Categoría:", self.category_combo)

        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Ej: python, libraries, data-science (separados por comas)")
        self.tags_input.setStyleSheet(self._get_input_style())
        basic_layout.addRow("Tags (opcional):", self.tags_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Grupo: Dimensiones de Tabla
        dim_group = QGroupBox("Dimensiones de Tabla")
        dim_group.setStyleSheet(basic_group.styleSheet())
        dim_layout = QFormLayout()
        dim_layout.setSpacing(15)

        # Número de filas
        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setMinimum(1)
        self.rows_spinbox.setMaximum(100)
        self.rows_spinbox.setValue(10)
        self.rows_spinbox.setStyleSheet(self._get_spinbox_style())
        dim_layout.addRow("Número de Filas:", self.rows_spinbox)

        # Número de columnas
        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setMinimum(1)
        self.cols_spinbox.setMaximum(20)
        self.cols_spinbox.setValue(4)
        self.cols_spinbox.setStyleSheet(self._get_spinbox_style())
        self.cols_spinbox.valueChanged.connect(self.update_columns_table)
        dim_layout.addRow("Número de Columnas:", self.cols_spinbox)

        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)

        # Grupo: Configuración de Columnas
        columns_group = QGroupBox("Configuración de Columnas")
        columns_group.setStyleSheet(basic_group.styleSheet())
        columns_layout = QVBoxLayout()

        # Instrucciones
        columns_info = QLabel(
            "Define el nombre y tipo de cada columna. La IA generará datos según esta estructura."
        )
        columns_info.setWordWrap(True)
        columns_info.setStyleSheet("color: #aaaaaa; font-size: 9pt; margin-bottom: 10px;")
        columns_layout.addWidget(columns_info)

        # Tabla de columnas
        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(3)
        self.columns_table.setHorizontalHeaderLabels(["Nombre Columna", "Es URL", "Es Sensible"])
        self.columns_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.columns_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.columns_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.columns_table.setColumnWidth(1, 80)
        self.columns_table.setColumnWidth(2, 100)
        self.columns_table.setMaximumHeight(300)
        self.columns_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                gridline-color: #3d3d3d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #00d4ff;
                padding: 8px;
                border: 1px solid #3d3d3d;
                font-weight: bold;
            }
        """)
        self.columns_table.setAlternatingRowColors(True)
        columns_layout.addWidget(self.columns_table)

        columns_group.setLayout(columns_layout)
        layout.addWidget(columns_group)

        # Grupo: Contexto para IA
        context_group = QGroupBox("Contexto para la IA")
        context_group.setStyleSheet(basic_group.styleSheet())
        context_layout = QVBoxLayout()

        context_info = QLabel(
            "Describe qué datos quieres generar. Sé específico sobre el tipo de información, "
            "industria, características, etc."
        )
        context_info.setWordWrap(True)
        context_info.setStyleSheet("color: #aaaaaa; font-size: 9pt; margin-bottom: 10px;")
        context_layout.addWidget(context_info)

        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText(
            "Ejemplo:\n"
            "Genera librerías Python populares para data science.\n"
            "Incluye pandas, numpy, matplotlib, scikit-learn, etc.\n"
            "Las URLs deben ser reales y funcionales.\n"
            "Las descripciones deben ser concisas (máximo 60 caracteres)."
        )
        self.context_input.setMinimumHeight(120)
        self.context_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
                color: #cccccc;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        context_layout.addWidget(self.context_input)

        context_group.setLayout(context_layout)
        layout.addWidget(context_group)

        # Inicializar tabla de columnas
        self.update_columns_table()

        scroll.setWidget(container)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def update_columns_table(self):
        """Actualiza la tabla de columnas según el número seleccionado."""
        num_cols = self.cols_spinbox.value()
        self.columns_table.setRowCount(num_cols)

        for i in range(num_cols):
            # Nombre de columna (solo crear si no existe)
            if not self.columns_table.item(i, 0):
                name_item = QTableWidgetItem(f"Columna {i+1}")
                self.columns_table.setItem(i, 0, name_item)

            # Checkbox URL (solo crear si no existe)
            if not self.columns_table.cellWidget(i, 1):
                url_checkbox = QCheckBox()
                url_checkbox.setStyleSheet("margin-left: 25px;")
                self.columns_table.setCellWidget(i, 1, url_checkbox)

            # Checkbox Sensible (solo crear si no existe)
            if not self.columns_table.cellWidget(i, 2):
                sensitive_checkbox = QCheckBox()
                sensitive_checkbox.setStyleSheet("margin-left: 35px;")
                self.columns_table.setCellWidget(i, 2, sensitive_checkbox)

    def load_categories(self):
        """Carga las categorías desde la base de datos."""
        try:
            self.categories = self.db.get_categories()
            self.category_combo.clear()

            for category in self.categories:
                self.category_combo.addItem(
                    f"{category['icon']} {category['name']}",
                    category['id']
                )

            logger.info(f"Loaded {len(self.categories)} categories")
        except Exception as e:
            logger.error(f"Error loading categories: {e}")

    def get_config(self) -> AITablePromptConfig:
        """
        Retorna la configuración completa del prompt.

        Returns:
            AITablePromptConfig con toda la configuración
        """
        # Obtener categoría seleccionada
        category_id = self.category_combo.currentData()
        category_name = self.category_combo.currentText().split(' ', 1)[1] if self.category_combo.currentText() else ""

        # Obtener tags
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []

        # Obtener configuración de columnas
        columns_config = []
        for i in range(self.cols_spinbox.value()):
            name_item = self.columns_table.item(i, 0)
            url_checkbox = self.columns_table.cellWidget(i, 1)
            sensitive_checkbox = self.columns_table.cellWidget(i, 2)

            col_config = {
                'name': name_item.text() if name_item else f"Columna {i+1}",
                'is_url': url_checkbox.isChecked() if url_checkbox else False,
                'is_sensitive': sensitive_checkbox.isChecked() if sensitive_checkbox else False
            }
            columns_config.append(col_config)

        # Crear y retornar configuración
        config = AITablePromptConfig(
            table_name=self.table_name_input.text().strip(),
            category_id=category_id,
            category_name=category_name,
            user_context=self.context_input.toPlainText().strip(),
            expected_rows=self.rows_spinbox.value(),
            expected_cols=self.cols_spinbox.value(),
            columns_config=columns_config,
            tags=tags,
            auto_detect_sensitive=False,  # Ahora siempre False
            auto_detect_urls=False  # Ahora siempre False
        )

        return config

    def is_valid(self) -> bool:
        """Valida que todos los campos requeridos estén completos."""
        # Validar nombre de tabla
        if not self.table_name_input.text().strip():
            return False

        # Validar categoría seleccionada
        if self.category_combo.currentIndex() < 0:
            return False

        # Validar contexto
        if len(self.context_input.toPlainText().strip()) < 10:
            return False

        # Validar nombres de columnas
        for i in range(self.cols_spinbox.value()):
            name_item = self.columns_table.item(i, 0)
            if not name_item or not name_item.text().strip():
                return False

        return True

    def get_validation_message(self) -> str:
        """Retorna mensaje de validación."""
        if not self.table_name_input.text().strip():
            return "Por favor ingresa un nombre para la tabla."

        if self.category_combo.currentIndex() < 0:
            return "Por favor selecciona una categoría."

        if len(self.context_input.toPlainText().strip()) < 10:
            return "Por favor describe el contexto (mínimo 10 caracteres)."

        # Validar nombres de columnas
        for i in range(self.cols_spinbox.value()):
            name_item = self.columns_table.item(i, 0)
            if not name_item or not name_item.text().strip():
                return f"Por favor ingresa un nombre para la columna {i+1}."

        return "Configuración válida."

    def _get_input_style(self) -> str:
        """Estilo para inputs de texto."""
        return """
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """

    def _get_combo_style(self) -> str:
        """Estilo para combobox."""
        return """
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
                font-size: 10pt;
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
        """

    def _get_spinbox_style(self) -> str:
        """Estilo para spinbox."""
        return """
            QSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: #cccccc;
                font-size: 10pt;
            }
            QSpinBox:focus {
                border: 1px solid #007acc;
            }
        """
