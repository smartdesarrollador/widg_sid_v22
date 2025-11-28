# -*- coding: utf-8 -*-
"""
Image Search Panel - Advanced Filters

Panel de búsqueda y filtros avanzados para la galería de imágenes.

Incluye:
- Búsqueda en tiempo real con debounce
- Filtros por categoría y tags
- Filtros avanzados: fecha, tamaño
- Contador de resultados
- Reset individual de filtros
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class ImageSearchPanel(QWidget):
    """
    Panel de búsqueda y filtros avanzados para galería de imágenes

    Características:
    - Búsqueda en tiempo real (debounce 300ms)
    - Filtros básicos: categoría, tags, favoritos
    - Filtros avanzados: rango de fechas, rango de tamaño
    - Panel colapsable de filtros avanzados
    - Contador de resultados en tiempo real
    - Reset individual de cada filtro
    """

    # Señales
    filters_changed = pyqtSignal(dict)  # Diccionario con filtros activos
    search_requested = pyqtSignal()  # Solicitar búsqueda inmediata
    filters_cleared = pyqtSignal()  # Todos los filtros limpiados

    def __init__(self, db_manager, parent=None):
        """
        Inicializar panel de búsqueda

        Args:
            db_manager: Instancia de DBManager para obtener categorías y tags
            parent: Widget padre
        """
        super().__init__(parent)

        self.db = db_manager
        self.active_filters = {}
        self.categories = []
        self.all_tags = []
        self.advanced_panel_visible = False
        self.result_count = 0

        # Timer para debounce de búsqueda
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_filters_changed)

        self.init_ui()
        self.load_filter_options()

    def init_ui(self):
        """
        Inicializar interfaz

        Layout:
        - Fila 1: Búsqueda de texto
        - Fila 2: Filtros básicos (categoría, tags, favoritos)
        - Fila 3: Toggle filtros avanzados
        - Panel colapsable: Filtros avanzados
        - Fila final: Resultados y botones
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        # Fila 1: Búsqueda de texto
        search_layout = self._create_search_input()
        main_layout.addLayout(search_layout)

        # Fila 2: Filtros básicos
        basic_filters_layout = self._create_basic_filters()
        main_layout.addLayout(basic_filters_layout)

        # Fila 3: Toggle filtros avanzados
        toggle_layout = self._create_advanced_toggle()
        main_layout.addLayout(toggle_layout)

        # Panel de filtros avanzados (colapsable)
        self.advanced_panel = self._create_advanced_filters()
        self.advanced_panel.setVisible(False)
        main_layout.addWidget(self.advanced_panel)

        # Fila final: Contador de resultados y botones
        actions_layout = self._create_actions_bar()
        main_layout.addLayout(actions_layout)

        # Estilos
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                font-size: 9pt;
                color: #cccccc;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e0e0e0;
                font-size: 9pt;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
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
            QPushButton#clearButton {
                background-color: #d32f2f;
                border: 1px solid #d32f2f;
            }
            QPushButton#clearButton:hover {
                background-color: #e53935;
            }
            QPushButton#resetFilterBtn {
                background-color: transparent;
                border: none;
                padding: 2px;
                font-size: 8pt;
                min-width: 20px;
                max-width: 20px;
            }
            QPushButton#resetFilterBtn:hover {
                background-color: #4d4d4d;
            }
            QCheckBox {
                spacing: 8px;
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
            }
            #advancedPanel {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 15px;
            }
            #resultCounter {
                color: #007acc;
                font-weight: bold;
                font-size: 10pt;
            }
        """)

    def _create_search_input(self) -> QHBoxLayout:
        """
        Crear campo de búsqueda con debounce

        Returns:
            Layout con búsqueda
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Label
        label = QLabel("🔍 Buscar:")
        label.setFixedWidth(90)
        font = QFont()
        font.setBold(True)
        label.setFont(font)

        # Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o descripción...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)

        # Reset button
        reset_btn = QPushButton("✕")
        reset_btn.setObjectName("resetFilterBtn")
        reset_btn.setToolTip("Limpiar búsqueda")
        reset_btn.clicked.connect(lambda: self.search_input.clear())
        reset_btn.setFixedSize(24, 24)

        layout.addWidget(label)
        layout.addWidget(self.search_input)
        layout.addWidget(reset_btn)

        return layout

    def _create_basic_filters(self) -> QGridLayout:
        """
        Crear filtros básicos: categoría, tags, favoritos

        Returns:
            Layout con filtros básicos
        """
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        # Filtro por categoría
        category_label = QLabel("📁 Categoría:")
        category_label.setFixedWidth(90)

        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(200)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)

        category_reset = QPushButton("✕")
        category_reset.setObjectName("resetFilterBtn")
        category_reset.setToolTip("Restablecer categoría")
        category_reset.clicked.connect(lambda: self.category_combo.setCurrentIndex(0))
        category_reset.setFixedSize(24, 24)

        layout.addWidget(category_label, 0, 0)
        layout.addWidget(self.category_combo, 0, 1)
        layout.addWidget(category_reset, 0, 2)

        # Filtro por tags
        tags_label = QLabel("🏷️ Tags:")
        tags_label.setFixedWidth(70)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3...")
        self.tags_input.setMinimumWidth(200)
        self.tags_input.textChanged.connect(self._on_tags_changed)

        tags_reset = QPushButton("✕")
        tags_reset.setObjectName("resetFilterBtn")
        tags_reset.setToolTip("Limpiar tags")
        tags_reset.clicked.connect(lambda: self.tags_input.clear())
        tags_reset.setFixedSize(24, 24)

        layout.addWidget(tags_label, 0, 3)
        layout.addWidget(self.tags_input, 0, 4)
        layout.addWidget(tags_reset, 0, 5)

        # Checkbox favoritos
        self.favorites_checkbox = QCheckBox("⭐ Solo Favoritos")
        self.favorites_checkbox.stateChanged.connect(self._on_favorites_changed)

        layout.addWidget(self.favorites_checkbox, 1, 0, 1, 2)

        return layout

    def _create_advanced_toggle(self) -> QHBoxLayout:
        """
        Crear botón toggle para mostrar/ocultar filtros avanzados

        Returns:
            Layout con toggle
        """
        layout = QHBoxLayout()

        self.advanced_toggle_btn = QPushButton("▼ Filtros Avanzados")
        self.advanced_toggle_btn.setCheckable(True)
        self.advanced_toggle_btn.setMaximumWidth(180)
        self.advanced_toggle_btn.clicked.connect(self._toggle_advanced_filters)

        layout.addWidget(self.advanced_toggle_btn)
        layout.addStretch()

        return layout

    def _create_advanced_filters(self) -> QFrame:
        """
        Crear panel colapsable con filtros avanzados

        Filtros:
        - Rango de fechas (desde - hasta)
        - Rango de tamaño de archivo (min - max)

        Returns:
            Widget con filtros avanzados
        """
        panel = QFrame()
        panel.setObjectName("advancedPanel")

        layout = QGridLayout(panel)
        layout.setSpacing(12)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        # Título
        title = QLabel("🔧 Filtros Avanzados")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        title.setFont(font)
        layout.addWidget(title, 0, 0, 1, 6)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3d3d3d;")
        separator.setFixedHeight(1)
        layout.addWidget(separator, 1, 0, 1, 6)

        # Filtro de fechas
        date_label = QLabel("📅 Rango de Fechas:")
        date_label.setFixedWidth(140)

        from_label = QLabel("Desde:")
        from_label.setFixedWidth(50)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.dateChanged.connect(self._on_date_changed)

        to_label = QLabel("Hasta:")
        to_label.setFixedWidth(50)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.dateChanged.connect(self._on_date_changed)

        date_reset = QPushButton("✕")
        date_reset.setObjectName("resetFilterBtn")
        date_reset.setToolTip("Restablecer fechas")
        date_reset.clicked.connect(self._reset_date_filters)
        date_reset.setFixedSize(24, 24)

        # Checkbox para activar/desactivar filtro de fecha
        self.date_enabled = QCheckBox("Activar filtro de fecha")
        self.date_enabled.setChecked(False)
        self.date_enabled.stateChanged.connect(self._on_date_filter_toggled)

        # Deshabilitar date pickers por defecto
        self.date_from.setEnabled(False)
        self.date_to.setEnabled(False)

        layout.addWidget(date_label, 2, 0)
        layout.addWidget(from_label, 2, 1)
        layout.addWidget(self.date_from, 2, 2)
        layout.addWidget(to_label, 2, 3)
        layout.addWidget(self.date_to, 2, 4)
        layout.addWidget(date_reset, 2, 5)
        layout.addWidget(self.date_enabled, 3, 0, 1, 3)

        # Filtro de tamaño de archivo
        size_label = QLabel("📏 Tamaño de Archivo (MB):")
        size_label.setFixedWidth(140)

        min_label = QLabel("Mín:")
        min_label.setFixedWidth(50)

        self.size_min = QDoubleSpinBox()
        self.size_min.setRange(0.0, 10000.0)
        self.size_min.setValue(0.0)
        self.size_min.setDecimals(2)
        self.size_min.setSuffix(" MB")
        self.size_min.valueChanged.connect(self._on_size_changed)

        max_label = QLabel("Máx:")
        max_label.setFixedWidth(50)

        self.size_max = QDoubleSpinBox()
        self.size_max.setRange(0.0, 10000.0)
        self.size_max.setValue(100.0)
        self.size_max.setDecimals(2)
        self.size_max.setSuffix(" MB")
        self.size_max.valueChanged.connect(self._on_size_changed)

        size_reset = QPushButton("✕")
        size_reset.setObjectName("resetFilterBtn")
        size_reset.setToolTip("Restablecer tamaños")
        size_reset.clicked.connect(self._reset_size_filters)
        size_reset.setFixedSize(24, 24)

        # Checkbox para activar/desactivar filtro de tamaño
        self.size_enabled = QCheckBox("Activar filtro de tamaño")
        self.size_enabled.setChecked(False)
        self.size_enabled.stateChanged.connect(self._on_size_filter_toggled)

        # Deshabilitar size spinners por defecto
        self.size_min.setEnabled(False)
        self.size_max.setEnabled(False)

        layout.addWidget(size_label, 4, 0)
        layout.addWidget(min_label, 4, 1)
        layout.addWidget(self.size_min, 4, 2)
        layout.addWidget(max_label, 4, 3)
        layout.addWidget(self.size_max, 4, 4)
        layout.addWidget(size_reset, 4, 5)
        layout.addWidget(self.size_enabled, 5, 0, 1, 3)

        return panel

    def _create_actions_bar(self) -> QHBoxLayout:
        """
        Crear barra de acciones con contador de resultados y botones

        Returns:
            Layout con acciones
        """
        layout = QHBoxLayout()
        layout.setSpacing(15)

        # Contador de resultados
        self.result_counter_label = QLabel("Resultados: --")
        self.result_counter_label.setObjectName("resultCounter")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.result_counter_label.setFont(font)

        layout.addWidget(self.result_counter_label)
        layout.addStretch()

        # Botón de búsqueda inmediata
        self.search_btn = QPushButton("🔍 Buscar Ahora")
        self.search_btn.setMinimumWidth(140)
        self.search_btn.clicked.connect(self._search_now)

        # Botón limpiar todos los filtros
        self.clear_all_btn = QPushButton("🗑️ Limpiar Todos")
        self.clear_all_btn.setObjectName("clearButton")
        self.clear_all_btn.setMinimumWidth(140)
        self.clear_all_btn.clicked.connect(self.clear_all_filters)

        layout.addWidget(self.search_btn)
        layout.addWidget(self.clear_all_btn)

        return layout

    def load_filter_options(self):
        """Cargar opciones de filtros desde BD (categorías y tags)"""
        try:
            # Cargar categorías con imágenes
            self.categories = self.db.get_image_categories()

            self.category_combo.clear()
            self.category_combo.addItem("📂 Todas las categorías", None)

            for category in self.categories:
                icon = category.get('icon', '📁')
                name = category.get('name', 'Sin nombre')
                count = category.get('count', 0)
                category_id = category.get('id')

                display_text = f"{icon} {name} ({count})"
                self.category_combo.addItem(display_text, category_id)

            # Cargar tags únicos
            self.all_tags = self.db.get_image_tags()

            # Actualizar placeholder de tags con sugerencias
            if self.all_tags:
                sample_tags = ', '.join(self.all_tags[:3])
                self.tags_input.setPlaceholderText(f"Ej: {sample_tags}...")

            logger.info(f"Loaded {len(self.categories)} categories and {len(self.all_tags)} tags")

        except Exception as e:
            logger.error(f"Error loading filter options: {e}", exc_info=True)

    def get_current_filters(self) -> Dict:
        """
        Obtener filtros actualmente activos

        Returns:
            Diccionario con filtros activos
        """
        filters = {}

        # Búsqueda de texto
        search_text = self.search_input.text().strip()
        if search_text:
            filters['search_text'] = search_text

        # Categoría
        category_id = self.category_combo.currentData()
        if category_id is not None:
            filters['category_id'] = category_id

        # Tags
        tags_text = self.tags_input.text().strip()
        if tags_text:
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            if tags:
                filters['tags'] = tags

        # Favoritos
        if self.favorites_checkbox.isChecked():
            filters['is_favorite'] = True

        # Rango de fechas (solo si está activado)
        if self.date_enabled.isChecked():
            date_from = self.date_from.date().toPyDate()
            date_to = self.date_to.date().toPyDate()
            filters['date_from'] = date_from
            filters['date_to'] = date_to

        # Rango de tamaño (solo si está activado)
        if self.size_enabled.isChecked():
            size_min = self.size_min.value()
            size_max = self.size_max.value()

            # Convertir MB a bytes
            if size_min > 0:
                filters['min_size'] = int(size_min * 1024 * 1024)
            if size_max > 0 and size_max < 10000:
                filters['max_size'] = int(size_max * 1024 * 1024)

        return filters

    def clear_all_filters(self):
        """Limpiar todos los filtros a valores por defecto"""
        logger.info("Clearing all filters")

        # Búsqueda
        self.search_input.clear()

        # Categoría
        self.category_combo.setCurrentIndex(0)

        # Tags
        self.tags_input.clear()

        # Favoritos
        self.favorites_checkbox.setChecked(False)

        # Fechas
        self.date_enabled.setChecked(False)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())

        # Tamaños
        self.size_enabled.setChecked(False)
        self.size_min.setValue(0.0)
        self.size_max.setValue(100.0)

        # Emitir señal
        self.filters_cleared.emit()
        self._emit_filters_changed()

    def set_result_count(self, count: int):
        """
        Actualizar contador de resultados

        Args:
            count: Número de resultados
        """
        self.result_count = count
        self.result_counter_label.setText(f"Resultados: {count}")

    def _toggle_advanced_filters(self):
        """Toggle visibilidad de panel de filtros avanzados"""
        self.advanced_panel_visible = not self.advanced_panel_visible
        self.advanced_panel.setVisible(self.advanced_panel_visible)

        # Cambiar texto del botón
        if self.advanced_panel_visible:
            self.advanced_toggle_btn.setText("▲ Filtros Avanzados")
        else:
            self.advanced_toggle_btn.setText("▼ Filtros Avanzados")

        logger.debug(f"Advanced filters panel: {'visible' if self.advanced_panel_visible else 'hidden'}")

    def _on_search_text_changed(self, text: str):
        """
        Handler para cambios en búsqueda con debounce

        Args:
            text: Texto de búsqueda
        """
        # Reiniciar timer de 300ms
        self.search_timer.stop()
        self.search_timer.start(300)

    def _on_category_changed(self, index: int):
        """Handler para cambio de categoría"""
        self._emit_filters_changed()

    def _on_tags_changed(self, text: str):
        """Handler para cambio de tags"""
        # Aplicar debounce también a tags
        self.search_timer.stop()
        self.search_timer.start(300)

    def _on_favorites_changed(self, state: int):
        """Handler para checkbox de favoritos"""
        self._emit_filters_changed()

    def _on_date_filter_toggled(self, state: int):
        """Handler para activar/desactivar filtro de fecha"""
        enabled = state == Qt.CheckState.Checked.value
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
        self._emit_filters_changed()

    def _on_date_changed(self):
        """Handler para cambio de fechas"""
        if self.date_enabled.isChecked():
            self._emit_filters_changed()

    def _on_size_filter_toggled(self, state: int):
        """Handler para activar/desactivar filtro de tamaño"""
        enabled = state == Qt.CheckState.Checked.value
        self.size_min.setEnabled(enabled)
        self.size_max.setEnabled(enabled)
        self._emit_filters_changed()

    def _on_size_changed(self):
        """Handler para cambio de tamaños"""
        if self.size_enabled.isChecked():
            self._emit_filters_changed()

    def _reset_date_filters(self):
        """Restablecer filtros de fecha a valores por defecto"""
        self.date_enabled.setChecked(False)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self._emit_filters_changed()

    def _reset_size_filters(self):
        """Restablecer filtros de tamaño a valores por defecto"""
        self.size_enabled.setChecked(False)
        self.size_min.setValue(0.0)
        self.size_max.setValue(100.0)
        self._emit_filters_changed()

    def _emit_filters_changed(self):
        """Emitir señal de cambio de filtros con filtros actuales"""
        self.active_filters = self.get_current_filters()
        logger.debug(f"Filters changed: {self.active_filters}")
        self.filters_changed.emit(self.active_filters)

    def _search_now(self):
        """Ejecutar búsqueda inmediatamente (sin debounce)"""
        logger.info("Immediate search requested")
        self.search_timer.stop()
        self._emit_filters_changed()
        self.search_requested.emit()
