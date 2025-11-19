"""
Advanced Filter Panel Widget
Panel colapsable de filtros avanzados para el panel flotante
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QCheckBox, QButtonGroup, QRadioButton, QScrollArea,
    QSpinBox, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QDate, QTimer
from PyQt6.QtGui import QFont, QCursor
import sys
import json
import hashlib
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.item import ItemType

# Get logger
logger = logging.getLogger(__name__)


class AdvancedFilterPanel(QWidget):
    """
    Panel colapsable de filtros avanzados

    Señales:
        filters_changed: Emitida cuando cambian los filtros activos
        filters_cleared: Emitida cuando se limpian todos los filtros
        preset_saved: Emitida cuando se guarda un preset de filtros
    """

    # Señales
    filters_changed = pyqtSignal(dict)  # Emite diccionario de filtros activos
    filters_cleared = pyqtSignal()
    preset_saved = pyqtSignal(str, dict)  # nombre, filtros

    def __init__(self, parent=None):
        """
        Inicializar panel de filtros avanzados

        Args:
            parent: Widget padre
        """
        super().__init__(parent)

        # Estado del panel
        self.is_expanded = False
        self.active_filters = {}
        self.active_filters_count = 0

        # Estado de los botones de acción (acordeón)
        self.actions_expanded = False

        # Tags disponibles (se llenarán dinámicamente)
        self.available_tags = []  # Lista de todos los tags disponibles
        self.tag_checkboxes = {}  # Dict[str, QCheckBox]

        # Presets de filtros (Fase 6)
        self.filter_presets = {}  # Dict[str, dict] - nombre: filtros
        self.load_presets()  # Cargar presets guardados

        # Debouncing timer (Fase 7) - Evita aplicar filtros en cada cambio
        self.filter_debounce_timer = QTimer()
        self.filter_debounce_timer.setSingleShot(True)
        self.filter_debounce_timer.setInterval(300)  # 300ms de espera
        self.filter_debounce_timer.timeout.connect(self._apply_filters_delayed)

        # Indicador de estado de filtrado (Fase 7)
        self.is_filtering = False

        # Caché de resultados de filtrado (Fase 7)
        self.filter_cache = {}  # Dict[str, List[Item]] - hash de filtros: resultados
        self.last_filters_hash = None  # Hash de los últimos filtros aplicados
        self.cache_enabled = True  # Activar/desactivar caché

        # Altura del contenedor de filtros (0 cuando está colapsado)
        self.content_height = 0
        self.max_content_height = 750  # Altura máxima cuando está expandido (aumentada de 650 a 750)

        self.init_ui()

    def init_ui(self):
        """Inicializar la interfaz del usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header del panel (siempre visible)
        self.create_header()
        main_layout.addWidget(self.header_widget)

        # Contenedor de filtros (colapsable)
        self.content_widget = QFrame()
        self.content_widget.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: none;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        self.content_widget.setMaximumHeight(0)  # Inicialmente colapsado

        # Layout del contenedor de filtros
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 10, 5)  # Reducido para menos espacio
        self.content_layout.setSpacing(8)  # Reducido de 15 a 8

        # Agregar secciones de filtros (se implementarán en fases siguientes)
        self.create_filter_sections()

        main_layout.addWidget(self.content_widget)

    def create_header(self):
        """Crear el header colapsable del panel"""
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: none;
                border-bottom: 1px solid #3d3d3d;
            }
            QWidget:hover {
                background-color: #3d3d3d;
            }
        """)
        self.header_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.header_widget.setFixedHeight(30)  # Reducido de 40 a 30

        # Layout del header
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)  # Reducido de (15,8,15,8)
        header_layout.setSpacing(8)  # Reducido de 10 a 8

        # Icono de expandir/colapsar
        self.expand_icon = QLabel("🔽")
        self.expand_icon.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 10pt;
                background-color: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(self.expand_icon)

        # Título del panel
        self.title_label = QLabel("Filtros Avanzados")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10pt;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(self.title_label)

        # Badge con contador de filtros activos
        self.filters_badge = QLabel("")
        self.filters_badge.setStyleSheet("""
            QLabel {
                background-color: #007acc;
                color: #ffffff;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 9pt;
                font-weight: bold;
            }
        """)
        self.filters_badge.setVisible(False)
        header_layout.addWidget(self.filters_badge)

        # Indicador de "Filtrando..." (Fase 7)
        self.filtering_label = QLabel("⏳ Filtrando...")
        self.filtering_label.setStyleSheet("""
            QLabel {
                color: #ffa500;
                font-size: 9pt;
                font-style: italic;
                background-color: transparent;
                border: none;
                padding: 0px 5px;
            }
        """)
        self.filtering_label.setVisible(False)
        header_layout.addWidget(self.filtering_label)

        header_layout.addStretch()

        # Botón de cerrar/limpiar filtros (solo visible cuando hay filtros activos)
        self.clear_button = QPushButton("×")
        self.clear_button.setFixedSize(24, 24)
        self.clear_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                font-size: 14pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 0.3);
                border: 1px solid rgba(255, 100, 100, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 100, 100, 0.5);
            }
        """)
        self.clear_button.setVisible(False)
        self.clear_button.setToolTip("Limpiar todos los filtros")
        self.clear_button.clicked.connect(self.clear_all_filters)
        header_layout.addWidget(self.clear_button)

        # Conectar click del header para expandir/colapsar
        self.header_widget.mousePressEvent = lambda event: self.toggle_expand()

    def create_filter_sections(self):
        """Crear las secciones de filtros"""
        # Sección 1: Tipo de Item
        self.create_type_filter_section()

        # Separador
        self.content_layout.addWidget(self.create_separator())

        # Sección 2: Estado
        self.create_state_filter_section()

        # Separador
        self.content_layout.addWidget(self.create_separator())

        # Sección 3: Uso y Popularidad (Fase 3)
        self.create_usage_filter_section()

        # Separador
        self.content_layout.addWidget(self.create_separator())

        # Sección 4: Tags (Fase 4)
        self.create_tags_filter_section()

        # Separador
        self.content_layout.addWidget(self.create_separator())

        # Sección 5: Fechas (Fase 5)
        self.create_dates_filter_section()

        # Separador
        self.content_layout.addWidget(self.create_separator())

        # Botones de acción
        self.create_action_buttons()

        # Spacer al final
        self.content_layout.addStretch()

    def create_separator(self):
        """Crear línea separadora entre secciones"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: #3d3d3d;
                max-height: 1px;
            }
        """)
        return separator

    def create_type_filter_section(self):
        """Crear sección de filtro por tipo de item"""
        # Título de la sección
        title = QLabel("TIPO DE ITEM")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 9pt;
                font-weight: bold;
                padding: 0px 0px 5px 0px;
            }
        """)
        self.content_layout.addWidget(title)

        # Contenedor de checkboxes horizontal
        type_layout = QHBoxLayout()
        type_layout.setSpacing(15)

        # Checkboxes para cada tipo
        self.type_checkboxes = {}

        for item_type in ItemType:
            checkbox = QCheckBox(item_type.value.upper())
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #cccccc;
                    font-size: 10pt;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #3d3d3d;
                    border-radius: 3px;
                    background-color: #2d2d2d;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #007acc;
                }
                QCheckBox::indicator:checked {
                    background-color: #007acc;
                    border: 2px solid #007acc;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAuNSAzTDQuNSA5IDEuNSA2IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
                }
            """)
            checkbox.stateChanged.connect(self.on_filter_changed)
            self.type_checkboxes[item_type.value] = checkbox
            type_layout.addWidget(checkbox)

        type_layout.addStretch()
        self.content_layout.addLayout(type_layout)

    def create_state_filter_section(self):
        """Crear sección de filtro por estado"""
        # Título de la sección
        title = QLabel("ESTADO Y ATRIBUTOS")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 9pt;
                font-weight: bold;
                padding: 0px 0px 5px 0px;
            }
        """)
        self.content_layout.addWidget(title)

        # Checkboxes de estado (vertical)
        state_layout = QVBoxLayout()
        state_layout.setSpacing(8)

        # Checkbox: Solo Favoritos
        self.favorites_checkbox = QCheckBox("⭐ Solo Favoritos")
        self.favorites_checkbox.setStyleSheet(self.get_checkbox_style())
        self.favorites_checkbox.stateChanged.connect(self.on_filter_changed)
        state_layout.addWidget(self.favorites_checkbox)

        # Checkbox: Solo Sensibles
        self.sensitive_checkbox = QCheckBox("🔒 Solo Sensibles")
        self.sensitive_checkbox.setStyleSheet(self.get_checkbox_style())
        self.sensitive_checkbox.stateChanged.connect(self.on_filter_changed)
        state_layout.addWidget(self.sensitive_checkbox)

        # Checkbox: Sin Tags
        self.no_tags_checkbox = QCheckBox("🏷️ Sin Tags")
        self.no_tags_checkbox.setStyleSheet(self.get_checkbox_style())
        self.no_tags_checkbox.stateChanged.connect(self.on_filter_changed)
        state_layout.addWidget(self.no_tags_checkbox)

        # Checkbox: Solo Listas
        self.lists_only_checkbox = QCheckBox("📝 Solo Listas")
        self.lists_only_checkbox.setStyleSheet(self.get_checkbox_style())
        self.lists_only_checkbox.stateChanged.connect(self.on_filter_changed)
        state_layout.addWidget(self.lists_only_checkbox)

        self.content_layout.addLayout(state_layout)

    def create_usage_filter_section(self):
        """Crear sección de filtro por uso y popularidad (Fase 3)"""
        from PyQt6.QtWidgets import QSpinBox, QComboBox

        # Título de la sección
        title = QLabel("USO Y POPULARIDAD")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 9pt;
                font-weight: bold;
                padding: 0px 0px 5px 0px;
            }
        """)
        self.content_layout.addWidget(title)

        # Layout vertical para los controles
        usage_layout = QVBoxLayout()
        usage_layout.setSpacing(10)

        # --- Filtro por número de usos ---
        use_count_layout = QHBoxLayout()
        use_count_layout.setSpacing(8)

        use_count_label = QLabel("Usos:")
        use_count_label.setStyleSheet("color: #cccccc; font-size: 10pt;")
        use_count_layout.addWidget(use_count_label)

        # Combobox para operador
        self.use_count_operator = QComboBox()
        self.use_count_operator.addItems(["-", ">", ">=", "<", "<=", "="])
        self.use_count_operator.setCurrentIndex(0)  # "-" por defecto (sin filtro)
        self.use_count_operator.setFixedWidth(50)
        self.use_count_operator.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
            }
        """)
        self.use_count_operator.currentIndexChanged.connect(self.on_filter_changed)
        use_count_layout.addWidget(self.use_count_operator)

        # SpinBox para valor
        self.use_count_value = QSpinBox()
        self.use_count_value.setMinimum(0)
        self.use_count_value.setMaximum(9999)
        self.use_count_value.setValue(0)
        self.use_count_value.setFixedWidth(80)
        self.use_count_value.setStyleSheet("""
            QSpinBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            QSpinBox:hover {
                border: 1px solid #007acc;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3d3d3d;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #007acc;
            }
        """)
        self.use_count_value.valueChanged.connect(self.on_filter_changed)
        use_count_layout.addWidget(self.use_count_value)

        use_count_layout.addStretch()
        usage_layout.addLayout(use_count_layout)

        # --- Filtro por último uso ---
        last_used_layout = QHBoxLayout()
        last_used_layout.setSpacing(8)

        last_used_label = QLabel("Último uso:")
        last_used_label.setStyleSheet("color: #cccccc; font-size: 10pt;")
        last_used_layout.addWidget(last_used_label)

        # Combobox para presets de fechas
        self.last_used_preset = QComboBox()
        self.last_used_preset.addItems([
            "-",
            "Hoy",
            "Últimos 7 días",
            "Últimos 30 días",
            "Últimos 90 días",
            "Nunca usado"
        ])
        self.last_used_preset.setCurrentIndex(0)  # "-" por defecto
        self.last_used_preset.setFixedWidth(150)
        self.last_used_preset.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
            }
        """)
        self.last_used_preset.currentIndexChanged.connect(self.on_filter_changed)
        last_used_layout.addWidget(self.last_used_preset)

        last_used_layout.addStretch()
        usage_layout.addLayout(last_used_layout)

        # --- Ordenamiento ---
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(8)

        sort_label = QLabel("Ordenar por:")
        sort_label.setStyleSheet("color: #cccccc; font-size: 10pt;")
        sort_layout.addWidget(sort_label)

        # Combobox para ordenamiento
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItems([
            "-",
            "Más usados",
            "Menos usados",
            "Usados recientemente",
            "Más antiguos",
            "A-Z",
            "Z-A"
        ])
        self.sort_by_combo.setCurrentIndex(0)  # "-" por defecto
        self.sort_by_combo.setFixedWidth(150)
        self.sort_by_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
            }
        """)
        self.sort_by_combo.currentIndexChanged.connect(self.on_filter_changed)
        sort_layout.addWidget(self.sort_by_combo)

        sort_layout.addStretch()
        usage_layout.addLayout(sort_layout)

        self.content_layout.addLayout(usage_layout)

    def create_tags_filter_section(self):
        """Crear sección de filtro por tags (Fase 4)"""
        from PyQt6.QtWidgets import QScrollArea, QRadioButton

        # Título de la sección
        title = QLabel("FILTROS POR TAGS")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 9pt;
                font-weight: bold;
                padding: 0px 0px 5px 0px;
            }
        """)
        self.content_layout.addWidget(title)

        # Layout vertical para controles
        tags_layout = QVBoxLayout()
        tags_layout.setSpacing(8)

        # Lógica AND/OR
        logic_layout = QHBoxLayout()
        logic_layout.setSpacing(10)

        logic_label = QLabel("Lógica:")
        logic_label.setStyleSheet("color: #cccccc; font-size: 10pt;")
        logic_layout.addWidget(logic_label)

        # Radio buttons para AND/OR
        self.tags_logic_group = QButtonGroup(self)

        self.tags_or_radio = QRadioButton("OR (cualquiera)")
        self.tags_or_radio.setChecked(True)  # OR por defecto
        self.tags_or_radio.setStyleSheet("""
            QRadioButton {
                color: #cccccc;
                font-size: 10pt;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #3d3d3d;
                border-radius: 7px;
                background-color: #2d2d2d;
            }
            QRadioButton::indicator:hover {
                border: 2px solid #007acc;
            }
            QRadioButton::indicator:checked {
                background-color: #007acc;
                border: 2px solid #007acc;
            }
        """)
        self.tags_or_radio.toggled.connect(self.on_filter_changed)
        self.tags_logic_group.addButton(self.tags_or_radio)
        logic_layout.addWidget(self.tags_or_radio)

        self.tags_and_radio = QRadioButton("AND (todos)")
        self.tags_and_radio.setStyleSheet("""
            QRadioButton {
                color: #cccccc;
                font-size: 10pt;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #3d3d3d;
                border-radius: 7px;
                background-color: #2d2d2d;
            }
            QRadioButton::indicator:hover {
                border: 2px solid #007acc;
            }
            QRadioButton::indicator:checked {
                background-color: #007acc;
                border: 2px solid #007acc;
            }
        """)
        self.tags_and_radio.toggled.connect(self.on_filter_changed)
        self.tags_logic_group.addButton(self.tags_and_radio)
        logic_layout.addWidget(self.tags_and_radio)

        logic_layout.addStretch()
        tags_layout.addLayout(logic_layout)

        # Contenedor con scroll para los tags
        # Label informativo si no hay tags
        self.tags_info_label = QLabel("No hay tags disponibles. Agregar tags a los items para filtrar.")
        self.tags_info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 9pt;
                font-style: italic;
                padding: 10px;
            }
        """)
        self.tags_info_label.setWordWrap(True)
        tags_layout.addWidget(self.tags_info_label)

        # Área de scroll para checkboxes de tags (se llenará dinámicamente)
        self.tags_scroll_area = QScrollArea()
        self.tags_scroll_area.setWidgetResizable(True)
        self.tags_scroll_area.setMaximumHeight(120)  # Altura máxima del scroll
        self.tags_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tags_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tags_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                background-color: #252525;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
        """)
        self.tags_scroll_area.setVisible(False)  # Ocultar inicialmente

        # Widget contenedor para los checkboxes de tags
        self.tags_container = QWidget()
        self.tags_container.setStyleSheet("""
            QWidget {
                background-color: #252525;
            }
        """)
        self.tags_container_layout = QVBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(8, 8, 8, 8)
        self.tags_container_layout.setSpacing(6)
        self.tags_container_layout.addStretch()

        self.tags_scroll_area.setWidget(self.tags_container)
        tags_layout.addWidget(self.tags_scroll_area)

        self.content_layout.addLayout(tags_layout)

    def create_dates_filter_section(self):
        """Crear sección de filtro por fechas (Fase 5)"""
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate

        # Título de la sección
        title = QLabel("FILTROS POR FECHAS")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 9pt;
                font-weight: bold;
                padding: 0px 0px 5px 0px;
            }
        """)
        self.content_layout.addWidget(title)

        # Layout vertical para controles
        dates_layout = QVBoxLayout()
        dates_layout.setSpacing(10)

        # --- Filtro por fecha de creación ---
        created_layout = QHBoxLayout()
        created_layout.setSpacing(8)

        created_label = QLabel("Creado:")
        created_label.setStyleSheet("color: #cccccc; font-size: 10pt;")
        created_layout.addWidget(created_label)

        # Combobox para presets de created_at
        self.created_at_preset = QComboBox()
        self.created_at_preset.addItems([
            "-",
            "Hoy",
            "Esta semana",
            "Este mes",
            "Últimos 7 días",
            "Últimos 30 días",
            "Rango personalizado"
        ])
        self.created_at_preset.setCurrentIndex(0)  # "-" por defecto
        self.created_at_preset.setFixedWidth(150)
        self.created_at_preset.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #cccccc;
                selection-background-color: #007acc;
            }
        """)
        self.created_at_preset.currentIndexChanged.connect(self.on_created_preset_changed)
        created_layout.addWidget(self.created_at_preset)

        created_layout.addStretch()
        dates_layout.addLayout(created_layout)

        # Contenedor para rango personalizado (inicialmente oculto)
        self.custom_range_container = QWidget()
        self.custom_range_container.setMinimumHeight(100)  # Aumentado de 80 a 100
        custom_range_layout = QVBoxLayout(self.custom_range_container)
        custom_range_layout.setContentsMargins(20, 12, 0, 12)  # Más padding vertical
        custom_range_layout.setSpacing(15)  # Más espacio entre campos (de 12 a 15)

        # Fecha desde
        from_layout = QHBoxLayout()
        from_layout.setSpacing(8)

        from_label = QLabel("Desde:")
        from_label.setStyleSheet("color: #cccccc; font-size: 9pt;")
        from_layout.addWidget(from_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))  # 7 días atrás por defecto
        self.date_from.setFixedWidth(140)  # Aumentado de 120 a 140
        self.date_from.setMinimumHeight(28)  # Altura mínima para mejor visibilidad
        self.date_from.setStyleSheet("""
            QDateEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 10pt;
            }
            QDateEdit:hover {
                border: 1px solid #007acc;
            }
            QDateEdit::drop-down {
                background-color: #3d3d3d;
                border: none;
                width: 20px;
            }
            QDateEdit::down-arrow {
                image: none;
                border: none;
            }
        """)
        self.date_from.dateChanged.connect(self.on_filter_changed)
        from_layout.addWidget(self.date_from)
        from_layout.addStretch()

        custom_range_layout.addLayout(from_layout)

        # Fecha hasta
        to_layout = QHBoxLayout()
        to_layout.setSpacing(8)

        to_label = QLabel("Hasta:")
        to_label.setStyleSheet("color: #cccccc; font-size: 9pt;")
        to_layout.addWidget(to_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())  # Hoy por defecto
        self.date_to.setFixedWidth(140)  # Aumentado de 120 a 140
        self.date_to.setMinimumHeight(28)  # Altura mínima para mejor visibilidad
        self.date_to.setStyleSheet("""
            QDateEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 10pt;
            }
            QDateEdit:hover {
                border: 1px solid #007acc;
            }
            QDateEdit::drop-down {
                background-color: #3d3d3d;
                border: none;
                width: 20px;
            }
            QDateEdit::down-arrow {
                image: none;
                border: none;
            }
        """)
        self.date_to.dateChanged.connect(self.on_filter_changed)
        to_layout.addWidget(self.date_to)
        to_layout.addStretch()

        custom_range_layout.addLayout(to_layout)

        self.custom_range_container.setVisible(False)  # Ocultar por defecto
        dates_layout.addWidget(self.custom_range_container)

        self.content_layout.addLayout(dates_layout)

    def on_created_preset_changed(self):
        """Handler cuando cambia el preset de fecha de creación"""
        preset_text = self.created_at_preset.currentText()

        # Mostrar/ocultar rango personalizado
        if preset_text == "Rango personalizado":
            self.custom_range_container.setVisible(True)
        else:
            self.custom_range_container.setVisible(False)

        # Trigger filter change
        self.on_filter_changed()

    def create_action_buttons(self):
        """Crear botones de acción con efecto acordeón colapsable"""
        # Contenedor principal
        actions_container = QWidget()
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(0)

        # Header clickeable para expandir/colapsar
        actions_header = QWidget()
        actions_header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #3d3d3d;
            }
        """)
        actions_header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        actions_header.setFixedHeight(32)

        header_layout = QHBoxLayout(actions_header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(8)

        # Icono de acordeón
        self.actions_icon = QLabel("▶")
        self.actions_icon.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 10pt;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(self.actions_icon)

        # Título
        actions_title = QLabel("Acciones")
        actions_title.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10pt;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(actions_title)
        header_layout.addStretch()

        # Conectar click en el header
        actions_header.mousePressEvent = lambda event: self.toggle_actions()

        actions_layout.addWidget(actions_header)

        # Contenedor de botones (colapsable)
        self.actions_buttons_widget = QFrame()
        self.actions_buttons_widget.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-top: none;
                border-radius: 0 0 4px 4px;
            }
        """)
        self.actions_buttons_widget.setMaximumHeight(0)  # Inicialmente colapsado

        buttons_layout = QHBoxLayout(self.actions_buttons_widget)
        buttons_layout.setContentsMargins(10, 10, 10, 10)  # Aumentado de 8 a 10
        buttons_layout.setSpacing(10)  # Aumentado de 8 a 10

        # Botón: Limpiar Todo
        clear_all_btn = QPushButton("🗑️ Limpiar")
        clear_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
        """)
        clear_all_btn.clicked.connect(self.clear_all_filters)
        clear_all_btn.setToolTip("Limpiar todos los filtros")
        buttons_layout.addWidget(clear_all_btn)

        # Botón: Cargar Preset
        load_preset_btn = QPushButton("📁 Cargar")
        load_preset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        load_preset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #007acc;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
        """)
        load_preset_btn.clicked.connect(self.show_load_preset_dialog)
        load_preset_btn.setToolTip("Cargar preset guardado")
        buttons_layout.addWidget(load_preset_btn)

        # Botón: Guardar Preset
        save_preset_btn = QPushButton("💾 Guardar")
        save_preset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_preset_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        save_preset_btn.clicked.connect(self.show_save_preset_dialog)
        save_preset_btn.setToolTip("Guardar filtros actuales como preset")
        buttons_layout.addWidget(save_preset_btn)

        actions_layout.addWidget(self.actions_buttons_widget)

        self.content_layout.addWidget(actions_container)

    def toggle_actions(self):
        """Expandir/colapsar sección de acciones con animación"""
        self.actions_expanded = not self.actions_expanded

        # Actualizar icono
        if self.actions_expanded:
            self.actions_icon.setText("▼")
            target_height = 60  # Aumentado de 50 a 60 para más espacio
        else:
            self.actions_icon.setText("▶")
            target_height = 0

        # Animación
        self.actions_animation = QPropertyAnimation(self.actions_buttons_widget, b"maximumHeight")
        self.actions_animation.setDuration(200)
        self.actions_animation.setStartValue(self.actions_buttons_widget.maximumHeight())
        self.actions_animation.setEndValue(target_height)
        self.actions_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.actions_animation.start()

    def update_available_tags(self, items):
        """
        Actualizar la lista de tags disponibles desde los items actuales

        Args:
            items: Lista de items de la categoría actual
        """
        # Obtener todos los tags únicos de los items
        all_tags = set()
        for item in items:
            if hasattr(item, 'tags') and item.tags:
                all_tags.update(item.tags)

        # Convertir a lista ordenada
        self.available_tags = sorted(list(all_tags))

        # Limpiar checkboxes anteriores
        while self.tags_container_layout.count() > 1:  # Mantener el stretch al final
            item = self.tags_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.tag_checkboxes.clear()

        # Si no hay tags, mostrar mensaje informativo
        if not self.available_tags:
            self.tags_info_label.setVisible(True)
            self.tags_scroll_area.setVisible(False)
            return

        # Ocultar mensaje informativo y mostrar scroll area
        self.tags_info_label.setVisible(False)
        self.tags_scroll_area.setVisible(True)

        # Crear checkbox para cada tag
        for tag in self.available_tags:
            checkbox = QCheckBox(f"🏷️ {tag}")
            checkbox.setStyleSheet(self.get_checkbox_style())
            checkbox.stateChanged.connect(self.on_filter_changed)
            self.tag_checkboxes[tag] = checkbox
            self.tags_container_layout.insertWidget(
                self.tags_container_layout.count() - 1,
                checkbox
            )

    def get_checkbox_style(self):
        """Obtener estilo común para checkboxes"""
        return """
            QCheckBox {
                color: #cccccc;
                font-size: 10pt;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 2px solid #007acc;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAuNSAzTDQuNSA5IDEuNSA2IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }
        """

    def on_filter_changed(self):
        """
        Handler cuando cambia cualquier filtro

        Usa debouncing para evitar aplicar filtros en cada cambio (Fase 7).
        Espera 300ms de inactividad antes de aplicar los filtros.
        """
        # Mostrar indicador de "filtrando..."
        self.filtering_label.setVisible(True)

        # Reiniciar el timer de debouncing
        # Si ya estaba corriendo, se reinicia
        self.filter_debounce_timer.stop()
        self.filter_debounce_timer.start()

    def _get_filters_hash(self, filters: dict) -> str:
        """
        Genera un hash único para una combinación de filtros (Fase 7)

        Args:
            filters: Diccionario de filtros activos

        Returns:
            Hash MD5 de los filtros (string hexadecimal)
        """
        # Convertir filtros a JSON serializable
        from datetime import datetime

        def serialize_value(obj):
            """Convertir valores a formato serializable"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_value(v) for v in obj]
            else:
                return obj

        serializable_filters = serialize_value(filters)

        # Generar hash MD5
        filters_str = json.dumps(serializable_filters, sort_keys=True)
        return hashlib.md5(filters_str.encode()).hexdigest()

    def _apply_filters_delayed(self):
        """
        Aplica los filtros después del debouncing (Fase 7)

        Este método es llamado por el timer después de 300ms de inactividad.
        Incluye sistema de caché para evitar re-aplicar filtros idénticos.
        """
        # Recopilar filtros activos
        self.collect_active_filters()

        # Verificar si los filtros han cambiado usando hash
        current_hash = self._get_filters_hash(self.active_filters)

        if self.cache_enabled and current_hash == self.last_filters_hash:
            # Los filtros no han cambiado, no hacer nada
            self.filtering_label.setVisible(False)
            return

        # Actualizar hash de filtros
        self.last_filters_hash = current_hash

        # Aplicar filtros
        self.apply_filters()

        # Ocultar indicador de "filtrando..."
        self.filtering_label.setVisible(False)

    def toggle_expand(self):
        """Expandir o colapsar el panel con animación"""
        self.is_expanded = not self.is_expanded

        # Actualizar icono
        if self.is_expanded:
            self.expand_icon.setText("🔼")
            target_height = self.max_content_height
        else:
            self.expand_icon.setText("🔽")
            target_height = 0

        # Animación de expansión/colapso
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(250)  # 250ms
        self.animation.setStartValue(self.content_widget.maximumHeight())
        self.animation.setEndValue(target_height)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.start()

    def keyPressEvent(self, event):
        """
        Manejar atajos de teclado (Fase 7)

        Atajos disponibles:
        - Ctrl+F: Expandir/colapsar panel de filtros
        - Ctrl+Shift+C: Limpiar todos los filtros
        - Escape: Colapsar panel si está expandido
        """
        from PyQt6.QtCore import Qt

        # Ctrl+F: Toggle expandir/colapsar
        if event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.toggle_expand()
            event.accept()
            return

        # Ctrl+Shift+C: Limpiar todos los filtros
        if (event.key() == Qt.Key.Key_C and
            event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
            self.clear_all_filters()
            event.accept()
            return

        # Escape: Colapsar panel si está expandido
        if event.key() == Qt.Key.Key_Escape and self.is_expanded:
            self.toggle_expand()
            event.accept()
            return

        # Pasar evento al padre si no fue manejado
        super().keyPressEvent(event)

    def update_filters_badge(self):
        """Actualizar el badge con el contador de filtros activos"""
        count = self.active_filters_count

        if count > 0:
            self.filters_badge.setText(f"{count} activo{'s' if count > 1 else ''}")
            self.filters_badge.setVisible(True)
            self.clear_button.setVisible(True)

            # Actualizar título cuando está colapsado
            if not self.is_expanded:
                self.title_label.setText(f"Filtros ({count} activo{'s' if count > 1 else ''})")
        else:
            self.filters_badge.setVisible(False)
            self.clear_button.setVisible(False)
            self.title_label.setText("Filtros Avanzados")

    def apply_filters(self):
        """
        Aplicar los filtros actuales y emitir señal

        Este método recopila todos los filtros activos y emite la señal
        filters_changed con el diccionario de filtros.
        """
        # Contar filtros activos
        self.active_filters_count = len([v for v in self.active_filters.values() if v])

        # Actualizar UI
        self.update_filters_badge()

        # Emitir señal con los filtros
        self.filters_changed.emit(self.active_filters.copy())

    def collect_active_filters(self):
        """Recopilar todos los filtros activos de los widgets"""
        filters = {}

        # Filtros de tipo
        selected_types = []
        for type_name, checkbox in self.type_checkboxes.items():
            if checkbox.isChecked():
                selected_types.append(type_name.upper())

        if selected_types:
            filters['type'] = selected_types

        # Filtros de estado
        logger.debug(f"Favorites checkbox checked: {self.favorites_checkbox.isChecked()}")
        logger.debug(f"Sensitive checkbox checked: {self.sensitive_checkbox.isChecked()}")
        logger.debug(f"No tags checkbox checked: {self.no_tags_checkbox.isChecked()}")

        if self.favorites_checkbox.isChecked():
            filters['is_favorite'] = True

        if self.sensitive_checkbox.isChecked():
            filters['is_sensitive'] = True

        if self.no_tags_checkbox.isChecked():
            filters['has_tags'] = False

        if self.lists_only_checkbox.isChecked():
            filters['is_list'] = True

        logger.debug(f"Collected filters: {filters}")

        # Filtros de uso (Fase 3)
        # Filtro por número de usos
        operator = self.use_count_operator.currentText()
        if operator != "-":  # Si no está en "sin filtro"
            filters['use_count'] = {
                'operator': operator,
                'value': self.use_count_value.value()
            }

        # Filtro por último uso
        last_used_text = self.last_used_preset.currentText()
        if last_used_text != "-":
            # Mapear texto a preset del engine
            preset_map = {
                "Hoy": "today",
                "Últimos 7 días": "last_7_days",
                "Últimos 30 días": "last_30_days",
                "Últimos 90 días": "last_90_days",
                "Nunca usado": "never"
            }
            if last_used_text in preset_map:
                filters['last_used'] = {
                    'preset': preset_map[last_used_text]
                }

        # Ordenamiento (Fase 3)
        sort_text = self.sort_by_combo.currentText()
        if sort_text != "-":
            # Mapear texto a sort_by del engine
            sort_map = {
                "Más usados": "use_count_desc",
                "Menos usados": "use_count_asc",
                "Usados recientemente": "recent",
                "Más antiguos": "oldest",
                "A-Z": "label_asc",
                "Z-A": "label_desc"
            }
            if sort_text in sort_map:
                filters['sort_by'] = sort_map[sort_text]

        # Filtros de tags (Fase 4)
        selected_tags = []
        for tag, checkbox in self.tag_checkboxes.items():
            if checkbox.isChecked():
                selected_tags.append(tag)

        if selected_tags:
            # Determinar modo AND/OR
            mode = "OR" if self.tags_or_radio.isChecked() else "AND"
            filters['tags'] = {
                'values': selected_tags,
                'mode': mode
            }

        # Filtros de fechas (Fase 5)
        created_text = self.created_at_preset.currentText()
        if created_text != "-":
            if created_text == "Rango personalizado":
                # Usar rango personalizado
                from datetime import datetime
                from_date = self.date_from.date().toPyDate()
                to_date = self.date_to.date().toPyDate()

                # Convertir a datetime con horas (inicio y fin del día)
                from_datetime = datetime.combine(from_date, datetime.min.time())
                to_datetime = datetime.combine(to_date, datetime.max.time())

                filters['created_at'] = {
                    'custom_from': from_datetime,
                    'custom_to': to_datetime
                }
            else:
                # Mapear texto a preset del engine
                preset_map = {
                    "Hoy": "today",
                    "Esta semana": "this_week",
                    "Este mes": "this_month",
                    "Últimos 7 días": "last_7_days",
                    "Últimos 30 días": "last_30_days"
                }
                if created_text in preset_map:
                    filters['created_at'] = {
                        'preset': preset_map[created_text]
                    }

        # Actualizar diccionario de filtros activos
        self.active_filters = filters

    def clear_all_filters(self):
        """Limpiar todos los filtros activos"""
        # Resetear diccionario de filtros
        self.active_filters = {}
        self.active_filters_count = 0

        # Resetear widgets - Tipo
        for checkbox in self.type_checkboxes.values():
            checkbox.setChecked(False)

        # Resetear widgets - Estado
        self.favorites_checkbox.setChecked(False)
        self.sensitive_checkbox.setChecked(False)
        self.no_tags_checkbox.setChecked(False)
        self.lists_only_checkbox.setChecked(False)

        # Resetear widgets - Uso (Fase 3)
        self.use_count_operator.setCurrentIndex(0)  # "-"
        self.use_count_value.setValue(0)
        self.last_used_preset.setCurrentIndex(0)  # "-"
        self.sort_by_combo.setCurrentIndex(0)  # "-"

        # Resetear widgets - Tags (Fase 4)
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(False)
        self.tags_or_radio.setChecked(True)  # Volver a OR por defecto

        # Resetear widgets - Fechas (Fase 5)
        self.created_at_preset.setCurrentIndex(0)  # "-"
        self.custom_range_container.setVisible(False)  # Ocultar rango personalizado

        # Actualizar UI
        self.update_filters_badge()

        # Emitir señales
        self.filters_cleared.emit()
        self.filters_changed.emit({})

    def get_active_filters(self) -> dict:
        """
        Obtener los filtros activos actuales

        Returns:
            dict: Diccionario con los filtros activos
        """
        return self.active_filters.copy()

    def set_filters(self, filters: dict):
        """
        Establecer filtros programáticamente (usado para presets)

        Args:
            filters: Diccionario de filtros a aplicar
        """
        self.active_filters = filters.copy()

        # TODO: Actualizar widgets de filtros según el diccionario (Fase 2+)

        # Aplicar filtros
        self.apply_filters()

    # ============ Métodos de Presets (Fase 6) ============

    def load_presets(self):
        """Cargar presets guardados desde archivo JSON"""
        import json
        from pathlib import Path

        presets_file = Path.home() / ".widget_sidebar" / "filter_presets.json"

        if presets_file.exists():
            try:
                with open(presets_file, 'r', encoding='utf-8') as f:
                    self.filter_presets = json.load(f)
            except Exception as e:
                print(f"Error loading presets: {e}")
                self.filter_presets = {}
        else:
            self.filter_presets = {}

    def save_presets(self):
        """Guardar presets a archivo JSON"""
        import json
        from pathlib import Path

        presets_dir = Path.home() / ".widget_sidebar"
        presets_dir.mkdir(exist_ok=True)

        presets_file = presets_dir / "filter_presets.json"

        try:
            # Convertir datetime objects a strings para JSON
            serializable_presets = {}
            for name, filters in self.filter_presets.items():
                serializable_filters = self._make_json_serializable(filters)
                serializable_presets[name] = serializable_filters

            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def _make_json_serializable(self, obj):
        """Convertir objeto a formato serializable JSON"""
        from datetime import datetime

        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def show_save_preset_dialog(self):
        """Mostrar diálogo para guardar preset"""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox

        if not self.active_filters:
            QMessageBox.warning(
                self,
                "Sin Filtros",
                "No hay filtros activos para guardar.\n\nPor favor, configura algunos filtros primero."
            )
            return

        # Pedir nombre del preset
        name, ok = QInputDialog.getText(
            self,
            "Guardar Preset",
            "Nombre del preset:",
            text="Mi Preset"
        )

        if ok and name:
            # Guardar preset
            self.filter_presets[name] = self.active_filters.copy()
            self.save_presets()

            QMessageBox.information(
                self,
                "Preset Guardado",
                f"El preset '{name}' ha sido guardado exitosamente.\n\n"
                f"Filtros guardados: {len(self.active_filters)}"
            )

    def show_load_preset_dialog(self):
        """Mostrar diálogo para cargar/gestionar presets"""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
            QPushButton, QLabel, QMessageBox
        )

        if not self.filter_presets:
            QMessageBox.information(
                self,
                "Sin Presets",
                "No hay presets guardados.\n\nGuarda tus filtros actuales como preset primero."
            )
            return

        # Crear diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Cargar Preset")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)

        layout = QVBoxLayout(dialog)

        # Título
        title = QLabel("Selecciona un preset para cargar:")
        title.setStyleSheet("font-size: 11pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Lista de presets
        preset_list = QListWidget()
        preset_list.addItems(self.filter_presets.keys())
        preset_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)
        layout.addWidget(preset_list)

        # Botones
        buttons_layout = QHBoxLayout()

        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #c42b1c;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #a52a1a;
            }
        """)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        buttons_layout.addWidget(cancel_btn)

        load_btn = QPushButton("✅ Cargar")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0e6b0e;
            }
        """)
        buttons_layout.addWidget(load_btn)

        layout.addLayout(buttons_layout)

        # Handlers
        def load_preset():
            selected = preset_list.currentItem()
            if selected:
                preset_name = selected.text()
                filters = self.filter_presets[preset_name]
                self.set_filters(filters)
                dialog.accept()

        def delete_preset():
            selected = preset_list.currentItem()
            if selected:
                preset_name = selected.text()
                reply = QMessageBox.question(
                    dialog,
                    "Eliminar Preset",
                    f"¿Estás seguro de eliminar el preset '{preset_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    del self.filter_presets[preset_name]
                    self.save_presets()
                    preset_list.takeItem(preset_list.currentRow())

        load_btn.clicked.connect(load_preset)
        delete_btn.clicked.connect(delete_preset)
        cancel_btn.clicked.connect(dialog.reject)
        preset_list.itemDoubleClicked.connect(load_preset)

        dialog.exec()
