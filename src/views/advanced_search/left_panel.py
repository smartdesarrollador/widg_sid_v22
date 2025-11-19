"""
Left Panel - Panel izquierdo con tabs: Historial, Filtros, Ayuda
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel,
    QScrollArea, QPushButton, QCheckBox, QLineEdit,
    QHBoxLayout, QFrame, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
logger = logging.getLogger(__name__)


class HistoryPanel(QWidget):
    """Panel de historial de búsquedas recientes"""

    search_requested = pyqtSignal(str, str)  # query, mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []  # List of recent searches
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("Búsquedas Recientes")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(header)

        # Scroll area for history items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        # Container for history items
        self.history_container = QWidget()
        self.history_container.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(5)

        # Empty state
        self.empty_label = QLabel("No hay búsquedas recientes")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 30px;
            }
        """)
        self.history_layout.addWidget(self.empty_label)

        self.history_layout.addStretch()

        scroll.setWidget(self.history_container)
        layout.addWidget(scroll)

    def add_search(self, query, mode, result_count):
        """Add a search to history"""
        if not query.strip():
            return

        # Wrap all widget access in try-except to handle deleted widgets
        try:
            # Remove empty label if present
            self.empty_label.setVisible(False)

            # Create history item button
            item = QPushButton(f"🔍 {query}")
            item.setToolTip(f"Modo: {mode.upper()}\nResultados: {result_count}")
            item.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    padding: 8px;
                    text-align: left;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    border-color: #f093fb;
                }
            """)
            item.clicked.connect(lambda: self._on_history_clicked(query, mode))

            # Insert at top
            self.history_layout.insertWidget(0, item)

            # Limit history to 10 items
            if self.history_layout.count() > 11:  # 10 + stretch
                widget = self.history_layout.itemAt(10).widget()
                if widget:
                    widget.deleteLater()
        except RuntimeError:
            # Widget has been deleted, ignore silently
            logger.debug(f"Cannot add search to history - widgets deleted")

    def _on_history_clicked(self, query, mode):
        """Handle history item click"""
        logger.info(f"History item clicked: {query}")
        self.search_requested.emit(query, mode)

    def clear_history(self):
        """Clear all history"""
        # Remove all buttons except empty label
        while self.history_layout.count() > 1:
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.empty_label.setVisible(True)


class FiltersPanel(QWidget):
    """Panel de filtros avanzados"""

    filters_changed = pyqtSignal(dict)  # filters dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Header
        header = QLabel("Filtros Avanzados")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        # Item Type filters
        type_group = self._create_filter_group("Tipo de Item", [
            ("💻 Código", "CODE"),
            ("🌐 URL", "URL"),
            ("📁 Ruta", "PATH"),
            ("📝 Texto", "TEXT")
        ])
        container_layout.addWidget(type_group)

        # State filters
        state_group = self._create_filter_group("Estado", [
            ("⭐ Favoritos", "favorite"),
            ("🔒 Sensibles", "sensitive"),
        ])
        container_layout.addWidget(state_group)

        # Date filters
        date_group = self._create_date_filter_group()
        container_layout.addWidget(date_group)

        # Apply button
        apply_btn = QPushButton("Aplicar Filtros")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #f093fb;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6ec7;
            }
            QPushButton:pressed {
                background-color: #d080e0;
            }
        """)
        apply_btn.clicked.connect(self._on_apply_filters)
        container_layout.addWidget(apply_btn)

        # Clear button
        clear_btn = QPushButton("Limpiar Filtros")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_filters)
        container_layout.addWidget(clear_btn)

        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_filter_group(self, title, options):
        """Create a filter group with checkboxes"""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #f093fb;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        group_layout.addWidget(title_label)

        # Checkboxes
        self.filter_checkboxes = getattr(self, 'filter_checkboxes', {})
        for label, value in options:
            checkbox = QCheckBox(label)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #ffffff;
                    font-size: 11px;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #3a3a3a;
                    border-radius: 3px;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background-color: #f093fb;
                    border-color: #f093fb;
                }
                QCheckBox::indicator:hover {
                    border-color: #f093fb;
                }
            """)
            self.filter_checkboxes[value] = checkbox
            group_layout.addWidget(checkbox)

        return group

    def _create_date_filter_group(self):
        """Create date filter group with date range pickers"""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        # Title
        title_label = QLabel("📅 Filtro por Fechas")
        title_label.setStyleSheet("""
            QLabel {
                color: #f093fb;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        group_layout.addWidget(title_label)

        # Enable date filter checkbox
        self.date_filter_enabled = QCheckBox("Habilitar filtro de fechas")
        self.date_filter_enabled.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #3a3a3a;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #f093fb;
                border-color: #f093fb;
            }
            QCheckBox::indicator:hover {
                border-color: #f093fb;
            }
        """)
        self.date_filter_enabled.stateChanged.connect(self._on_date_filter_toggled)
        group_layout.addWidget(self.date_filter_enabled)

        # Date range container
        self.date_range_container = QWidget()
        date_range_layout = QVBoxLayout(self.date_range_container)
        date_range_layout.setContentsMargins(0, 5, 0, 0)
        date_range_layout.setSpacing(8)

        # Fecha desde
        desde_layout = QVBoxLayout()
        desde_layout.setSpacing(4)
        desde_label = QLabel("Desde:")
        desde_label.setStyleSheet("color: #888888; font-size: 10px;")
        desde_layout.addWidget(desde_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))  # Default: 1 mes atrás
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setStyleSheet("""
            QDateEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
            }
            QDateEdit:hover {
                border-color: #f093fb;
            }
            QDateEdit::drop-down {
                border: none;
                padding-right: 8px;
            }
            QDateEdit::down-arrow {
                image: none;
                border: none;
            }
        """)
        desde_layout.addWidget(self.date_from)
        date_range_layout.addLayout(desde_layout)

        # Fecha hasta
        hasta_layout = QVBoxLayout()
        hasta_layout.setSpacing(4)
        hasta_label = QLabel("Hasta:")
        hasta_label.setStyleSheet("color: #888888; font-size: 10px;")
        hasta_layout.addWidget(hasta_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())  # Default: hoy
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setStyleSheet("""
            QDateEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
            }
            QDateEdit:hover {
                border-color: #f093fb;
            }
            QDateEdit::drop-down {
                border: none;
                padding-right: 8px;
            }
            QDateEdit::down-arrow {
                image: none;
                border: none;
            }
        """)
        hasta_layout.addWidget(self.date_to)
        date_range_layout.addLayout(hasta_layout)

        # Date field selector (created_at or last_used)
        field_layout = QVBoxLayout()
        field_layout.setSpacing(4)
        field_label = QLabel("Filtrar por:")
        field_label.setStyleSheet("color: #888888; font-size: 10px;")
        field_layout.addWidget(field_label)

        self.date_field_created = QCheckBox("📝 Fecha de creación")
        self.date_field_created.setChecked(True)
        self.date_field_created.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 10px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #3a3a3a;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #f093fb;
                border-color: #f093fb;
            }
        """)
        field_layout.addWidget(self.date_field_created)

        self.date_field_last_used = QCheckBox("⏰ Última vez usado")
        self.date_field_last_used.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 10px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #3a3a3a;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #f093fb;
                border-color: #f093fb;
            }
        """)
        field_layout.addWidget(self.date_field_last_used)

        date_range_layout.addLayout(field_layout)

        # Initially disable date range widgets
        self.date_range_container.setEnabled(False)

        group_layout.addWidget(self.date_range_container)

        return group

    def _on_date_filter_toggled(self, state):
        """Enable/disable date range widgets"""
        self.date_range_container.setEnabled(state == Qt.CheckState.Checked.value)

    def _on_apply_filters(self):
        """Apply selected filters"""
        filters = {}

        # Collect item types
        item_types = []
        for type_key in ['CODE', 'URL', 'PATH', 'TEXT']:
            if type_key in self.filter_checkboxes and self.filter_checkboxes[type_key].isChecked():
                item_types.append(type_key)

        if item_types:
            filters['item_types'] = item_types

        # Collect state filters
        if 'favorite' in self.filter_checkboxes and self.filter_checkboxes['favorite'].isChecked():
            filters['is_favorite'] = True

        if 'sensitive' in self.filter_checkboxes and self.filter_checkboxes['sensitive'].isChecked():
            filters['is_sensitive'] = True

        # Collect date filters
        if self.date_filter_enabled.isChecked():
            date_filters = {}
            date_filters['date_from'] = self.date_from.date().toString('yyyy-MM-dd')
            date_filters['date_to'] = self.date_to.date().toString('yyyy-MM-dd')

            # Collect which fields to filter
            fields = []
            if self.date_field_created.isChecked():
                fields.append('created_at')
            if self.date_field_last_used.isChecked():
                fields.append('last_used')

            if fields:
                date_filters['fields'] = fields
                filters['date_range'] = date_filters

        logger.info(f"Filters applied: {filters}")
        self.filters_changed.emit(filters)

    def _on_clear_filters(self):
        """Clear all filters"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(False)

        # Clear date filters
        self.date_filter_enabled.setChecked(False)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.date_field_created.setChecked(True)
        self.date_field_last_used.setChecked(False)

        self.filters_changed.emit({})
        logger.info("Filters cleared")

    def get_active_filters(self):
        """Get currently active filters"""
        filters = {}

        item_types = []
        for type_key in ['CODE', 'URL', 'PATH', 'TEXT']:
            if type_key in self.filter_checkboxes and self.filter_checkboxes[type_key].isChecked():
                item_types.append(type_key)

        if item_types:
            filters['item_types'] = item_types

        if 'favorite' in self.filter_checkboxes and self.filter_checkboxes['favorite'].isChecked():
            filters['is_favorite'] = True

        if 'sensitive' in self.filter_checkboxes and self.filter_checkboxes['sensitive'].isChecked():
            filters['is_sensitive'] = True

        # Collect date filters
        if self.date_filter_enabled.isChecked():
            date_filters = {}
            date_filters['date_from'] = self.date_from.date().toString('yyyy-MM-dd')
            date_filters['date_to'] = self.date_to.date().toString('yyyy-MM-dd')

            # Collect which fields to filter
            fields = []
            if self.date_field_created.isChecked():
                fields.append('created_at')
            if self.date_field_last_used.isChecked():
                fields.append('last_used')

            if fields:
                date_filters['fields'] = fields
                filters['date_range'] = date_filters

        return filters


class TagsFilterPanel(QWidget):
    """Panel de filtro dinámico por tags basado en resultados de búsqueda"""

    tags_filter_changed = pyqtSignal(list)  # List of selected tags

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tag_checkboxes = {}  # tag_name -> QCheckBox
        self.available_tags = set()  # Tags from current results
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🏷️ Filtro por Tags")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        header_layout.addWidget(header)

        # Tag count badge
        self.tag_count_label = QLabel("(0)")
        self.tag_count_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                padding: 5px;
            }
        """)
        header_layout.addWidget(self.tag_count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Scroll area for tag checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
        """)

        # Container for tag checkboxes
        self.tags_container = QWidget()
        self.tags_container.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        self.tags_layout = QVBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(6)

        # Empty state
        self.empty_label = QLabel("No hay tags disponibles\n\nRealiza una búsqueda para\nver tags relacionados")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                padding: 30px 10px;
            }
        """)
        self.tags_layout.addWidget(self.empty_label)
        self.tags_layout.addStretch()

        scroll.setWidget(self.tags_container)
        layout.addWidget(scroll)

        # Action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)

        # Select all button
        self.select_all_btn = QPushButton("✓ Seleccionar Todos")
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #f093fb;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #555555;
                border-color: #2a2a2a;
            }
        """)
        self.select_all_btn.clicked.connect(self._on_select_all)
        self.select_all_btn.setEnabled(False)
        buttons_layout.addWidget(self.select_all_btn)

        # Deselect all button
        self.deselect_all_btn = QPushButton("✗ Deseleccionar Todos")
        self.deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #f093fb;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #555555;
                border-color: #2a2a2a;
            }
        """)
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        self.deselect_all_btn.setEnabled(False)
        buttons_layout.addWidget(self.deselect_all_btn)

        layout.addLayout(buttons_layout)

    def update_tags_from_results(self, results):
        """
        Extract unique tags from search results and create checkboxes

        Args:
            results: List of result dicts from AdvancedSearchEngine
        """
        logger.info(f"Updating tags filter from {len(results)} results")

        # Extract unique tags from results
        new_tags = set()
        for result in results:
            tags_str = result.get('tags', '')
            if tags_str:
                # Split tags by comma and clean whitespace
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                new_tags.update(tags)

        # Only update if tags changed
        if new_tags == self.available_tags:
            logger.debug("Tags unchanged, skipping update")
            return

        self.available_tags = new_tags
        logger.info(f"Found {len(new_tags)} unique tags")

        # Clear existing checkboxes
        self._clear_tag_checkboxes()

        if not new_tags:
            # Show empty state
            self.empty_label.setVisible(True)
            self.select_all_btn.setEnabled(False)
            self.deselect_all_btn.setEnabled(False)
            self.tag_count_label.setText("(0)")
            return

        # Hide empty state
        self.empty_label.setVisible(False)
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)

        # Create checkbox for each unique tag (sorted alphabetically)
        for tag in sorted(new_tags):
            checkbox = QCheckBox(f"🏷️  {tag}")
            checkbox.setChecked(True)  # All tags selected by default
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #ffffff;
                    font-size: 11px;
                    spacing: 5px;
                    padding: 4px 8px;
                    background-color: #2a2a2a;
                    border-radius: 4px;
                }
                QCheckBox:hover {
                    background-color: #3a3a3a;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #3a3a3a;
                    border-radius: 3px;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background-color: #f093fb;
                    border-color: #f093fb;
                }
                QCheckBox::indicator:hover {
                    border-color: #f093fb;
                }
            """)
            checkbox.stateChanged.connect(self._on_tag_checkbox_changed)

            self.tag_checkboxes[tag] = checkbox
            # Insert before stretch
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, checkbox)

        # Update count
        self.tag_count_label.setText(f"({len(new_tags)})")

    def _clear_tag_checkboxes(self):
        """Remove all tag checkboxes"""
        for checkbox in self.tag_checkboxes.values():
            checkbox.deleteLater()
        self.tag_checkboxes.clear()

    def _on_tag_checkbox_changed(self):
        """Handle tag checkbox state change"""
        selected_tags = self.get_selected_tags()
        logger.debug(f"Tags filter changed: {len(selected_tags)} tags selected")
        self.tags_filter_changed.emit(selected_tags)

    def _on_select_all(self):
        """Select all tag checkboxes"""
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(True)
        logger.info("All tags selected")

    def _on_deselect_all(self):
        """Deselect all tag checkboxes"""
        for checkbox in self.tag_checkboxes.values():
            checkbox.setChecked(False)
        logger.info("All tags deselected")

    def get_selected_tags(self):
        """Get list of currently selected tags"""
        return [tag for tag, checkbox in self.tag_checkboxes.items() if checkbox.isChecked()]

    def clear(self):
        """Clear all tags"""
        self._clear_tag_checkboxes()
        self.available_tags.clear()
        self.empty_label.setVisible(True)
        self.select_all_btn.setEnabled(False)
        self.deselect_all_btn.setEnabled(False)
        self.tag_count_label.setText("(0)")


class HelpPanel(QWidget):
    """Panel de ayuda con documentación FTS5"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("💡 Ayuda de Búsqueda")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 5px;
            }
        """)

        # Help content
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        help_layout.setContentsMargins(0, 0, 10, 0)
        help_layout.setSpacing(15)

        # Sections
        help_layout.addWidget(self._create_section(
            "🔍 Modos de Búsqueda",
            [
                ("Smart", "Intenta FTS5, fallback a Exact"),
                ("FTS5", "Búsqueda full-text rápida"),
                ("Exact", "Búsqueda exacta con LIKE")
            ]
        ))

        help_layout.addWidget(self._create_section(
            "⚡ Operadores FTS5",
            [
                ("git AND push", "Ambos términos presentes"),
                ("git OR svn", "Cualquiera de los dos"),
                ("git NOT pull", "Excluir término"),
                ('"git push"', "Frase exacta"),
                ("python*", "Wildcard (python, pythonic, etc.)")
            ]
        ))

        help_layout.addWidget(self._create_section(
            "🎯 Búsqueda por Columna",
            [
                ("label:docker", "Solo en título"),
                ("tags:python", "Solo en tags"),
                ("content:api", "Solo en contenido")
            ]
        ))

        help_layout.addWidget(self._create_section(
            "⌨️ Atajos de Teclado",
            [
                ("Ctrl+F", "Focus en búsqueda"),
                ("Escape", "Cerrar ventana"),
                ("F5", "Refrescar resultados")
            ]
        ))

        help_layout.addStretch()

        scroll.setWidget(help_widget)
        layout.addWidget(scroll)

    def _create_section(self, title, items):
        """Create a help section"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #f093fb;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        section_layout.addWidget(title_label)

        # Items
        for label, description in items:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)

            # Label (example)
            label_widget = QLabel(f"  {label}")
            label_widget.setStyleSheet("""
                QLabel {
                    color: #4ec9b0;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 11px;
                }
            """)
            item_layout.addWidget(label_widget)

            # Description
            desc_widget = QLabel(f"    → {description}")
            desc_widget.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 10px;
                }
            """)
            desc_widget.setWordWrap(True)
            item_layout.addWidget(desc_widget)

            section_layout.addLayout(item_layout)

        return section


class LeftPanel(QWidget):
    """Panel izquierdo con tabs: Historial, Filtros, Tags, Ayuda"""

    search_requested = pyqtSignal(str, str)  # query, mode (from history)
    filters_changed = pyqtSignal(dict)  # filters
    tags_filter_changed = pyqtSignal(list)  # selected tags

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #888888;
                padding: 8px 12px;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 60px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border-bottom: 2px solid #f093fb;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3a3a3a;
                color: #ffffff;
            }
        """)

        # Create panels
        self.history_panel = HistoryPanel()
        self.history_panel.search_requested.connect(self.search_requested)

        self.filters_panel = FiltersPanel()
        self.filters_panel.filters_changed.connect(self.filters_changed)

        self.tags_filter_panel = TagsFilterPanel()
        self.tags_filter_panel.tags_filter_changed.connect(self.tags_filter_changed)

        self.help_panel = HelpPanel()

        # Add tabs
        self.tabs.addTab(self.history_panel, "📜 Historial")
        self.tabs.addTab(self.filters_panel, "🎯 Filtros")
        self.tabs.addTab(self.tags_filter_panel, "🏷️ Tags")
        self.tabs.addTab(self.help_panel, "❓ Ayuda")

        layout.addWidget(self.tabs)

    def add_search_to_history(self, query, mode, result_count):
        """Add search to history panel"""
        self.history_panel.add_search(query, mode, result_count)

    def update_tags_from_results(self, results):
        """Update tags filter panel with results"""
        self.tags_filter_panel.update_tags_from_results(results)

    def get_active_filters(self):
        """Get currently active filters"""
        return self.filters_panel.get_active_filters()

    def get_selected_tags(self):
        """Get currently selected tags"""
        return self.tags_filter_panel.get_selected_tags()
