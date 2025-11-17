"""
Process Builder Window - Ventana maximizada para crear y editar procesos

Layout de 3 paneles:
- Panel izquierdo (25%): Filtros de items
- Panel central (35%): Items y listas disponibles
- Panel derecho (40%): Constructor del proceso
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QScrollArea,
                             QSplitter, QFrame, QComboBox, QSpinBox, QMessageBox,
                             QColorDialog, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor, QColor
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.process import Process, ProcessStep
from models.category import Category
from views.widgets.process_step_widget import ProcessStepWidget
from views.widgets.item_widget import ItemButton
from views.widgets.search_bar import SearchBar

logger = logging.getLogger(__name__)


class ProcessBuilderWindow(QWidget):
    """Ventana para crear y editar procesos"""

    # Signals
    process_saved = pyqtSignal(int)  # process_id
    window_closed = pyqtSignal()

    def __init__(self, config_manager=None, process_controller=None,
                 process_id=None, parent=None):
        """
        Initialize ProcessBuilderWindow

        Args:
            config_manager: ConfigManager instance
            process_controller: ProcessController instance
            process_id: ID of process to edit (None for new process)
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.process_controller = process_controller
        self.process_id = process_id
        self.editing_mode = process_id is not None

        # Current process being built/edited
        self.current_process = None

        # Available items for adding to process
        self.available_items = []
        self.filtered_items = []

        # Step widgets in constructor
        self.step_widgets = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI"""
        # Window properties
        self.setWindowTitle("Crear Proceso" if not self.editing_mode else "Editar Proceso")
        self.setWindowFlags(Qt.WindowType.Window)

        # Calculate window size (maximized with margin for sidebar)
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            # Leave 70px margin on right for sidebar
            window_width = screen_geom.width() - 80  # 70px sidebar + 10px gap
            window_height = int(screen_geom.height() * 0.9)
            self.resize(window_width, window_height)
            # Position at left edge
            self.move(0, int(screen_geom.height() * 0.05))

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === HEADER ===
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # === PROCESS INFO ===
        info_layout = self.create_process_info_section()
        main_layout.addLayout(info_layout)

        # === 3-PANEL LAYOUT ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel 1: Filters (25%)
        filter_panel = self.create_filter_panel()
        splitter.addWidget(filter_panel)

        # Panel 2: Available Items (35%)
        items_panel = self.create_items_panel()
        splitter.addWidget(items_panel)

        # Panel 3: Process Constructor (40%)
        constructor_panel = self.create_constructor_panel()
        splitter.addWidget(constructor_panel)

        # Set initial sizes
        total_width = self.width()
        splitter.setSizes([
            int(total_width * 0.25),
            int(total_width * 0.35),
            int(total_width * 0.40)
        ])

        main_layout.addWidget(splitter, stretch=1)

        # === FOOTER BUTTONS ===
        footer_layout = self.create_footer()
        main_layout.addLayout(footer_layout)

        # Apply global styles
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #007acc;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QScrollArea {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
        """)

    def create_header(self) -> QHBoxLayout:
        """Create header with title and close button"""
        layout = QHBoxLayout()

        # Title
        title = QLabel("Crear Proceso" if not self.editing_mode else "Editar Proceso")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18pt;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("✕ Cerrar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #e4475b;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return layout

    def create_process_info_section(self) -> QHBoxLayout:
        """Create process information section"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Process name
        name_label = QLabel("Nombre:")
        name_label.setFixedWidth(80)
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del proceso...")
        layout.addWidget(self.name_input, stretch=2)

        # Description
        desc_label = QLabel("Descripcion:")
        desc_label.setFixedWidth(80)
        layout.addWidget(desc_label)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descripcion opcional...")
        layout.addWidget(self.description_input, stretch=2)

        # Icon
        icon_label = QLabel("Icono:")
        icon_label.setFixedWidth(60)
        layout.addWidget(icon_label)

        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Emoji")
        self.icon_input.setMaxLength(2)
        self.icon_input.setFixedWidth(60)
        layout.addWidget(self.icon_input)

        # Color picker
        self.color_button = QPushButton("Color")
        self.color_button.setFixedWidth(80)
        self.color_button.clicked.connect(self.pick_color)
        self.selected_color = None
        layout.addWidget(self.color_button)

        return layout

    def create_filter_panel(self) -> QWidget:
        """Create filter panel (left panel)"""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Filtros")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #007acc;")
        layout.addWidget(title)

        # Category filter
        cat_label = QLabel("Categoria:")
        layout.addWidget(cat_label)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorias", None)
        self.category_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.category_combo)

        # Type filter
        type_label = QLabel("Tipo:")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos los tipos", None)
        self.type_combo.addItem("CODE", "CODE")
        self.type_combo.addItem("URL", "URL")
        self.type_combo.addItem("PATH", "PATH")
        self.type_combo.addItem("TEXT", "TEXT")
        self.type_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.type_combo)

        layout.addStretch()

        return panel

    def create_items_panel(self) -> QWidget:
        """Create available items panel (center panel)"""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Items Disponibles")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #007acc;")
        title_layout.addWidget(title)

        self.items_count_label = QLabel("(0)")
        self.items_count_label.setStyleSheet("color: #888888;")
        title_layout.addWidget(self.items_count_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Search bar
        self.items_search = SearchBar()
        self.items_search.search_changed.connect(self.on_search_changed)
        layout.addWidget(self.items_search)

        # Scroll area for items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container for items
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)
        self.items_layout.addStretch()

        scroll.setWidget(self.items_container)
        layout.addWidget(scroll)

        return panel

    def create_constructor_panel(self) -> QWidget:
        """Create process constructor panel (right panel)"""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Constructor del Proceso")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #00ff88;")
        title_layout.addWidget(title)

        self.steps_count_label = QLabel("(0 steps)")
        self.steps_count_label.setStyleSheet("color: #888888;")
        title_layout.addWidget(self.steps_count_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Info label
        info_label = QLabel("Haz doble clic en un item de la izquierda para agregarlo")
        info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 9pt;
                font-style: italic;
                padding: 5px;
            }
        """)
        layout.addWidget(info_label)

        # Scroll area for steps
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # Container for steps
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(5)
        self.steps_layout.addStretch()

        scroll.setWidget(self.steps_container)
        layout.addWidget(scroll)

        # Configuration section
        config_frame = QFrame()
        config_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        config_layout = QVBoxLayout(config_frame)

        config_title = QLabel("Configuracion de Ejecucion")
        config_title.setStyleSheet("font-weight: bold; color: #007acc;")
        config_layout.addWidget(config_title)

        # Delay between steps
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay entre steps (ms):"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 10000)
        self.delay_spinbox.setValue(500)
        self.delay_spinbox.setSingleStep(100)
        delay_layout.addWidget(self.delay_spinbox)
        delay_layout.addStretch()
        config_layout.addLayout(delay_layout)

        layout.addWidget(config_frame)

        return panel

    def create_footer(self) -> QHBoxLayout:
        """Create footer with action buttons"""
        layout = QHBoxLayout()

        layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("💾 Guardar Proceso")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ff88;
                color: #000000;
                font-size: 11pt;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #00cc70;
            }
        """)
        save_btn.clicked.connect(self.on_save_clicked)
        layout.addWidget(save_btn)

        return layout

    # ==================== DATA LOADING ====================

    def load_data(self):
        """Load data (items, categories, process if editing)"""
        if not self.config_manager:
            logger.warning("No config_manager available")
            return

        # Load categories for filter
        categories = self.config_manager.get_categories()
        for category in categories:
            self.category_combo.addItem(category.name, category.id)

        # Load all items
        self.load_all_items()

        # If editing, load process data
        if self.editing_mode and self.process_id:
            self.load_process_for_editing()

    def load_all_items(self):
        """Load all items from all categories"""
        if not self.config_manager:
            return

        self.available_items = []
        categories = self.config_manager.get_categories()

        for category in categories:
            # Get items from this category (excluding list items)
            items = [item for item in category.items if not item.is_list_item()]
            self.available_items.extend(items)

        logger.info(f"Loaded {len(self.available_items)} items")
        self.filtered_items = self.available_items.copy()
        self.display_items()

    def load_process_for_editing(self):
        """Load existing process data for editing"""
        if not self.process_controller:
            logger.error("No process_controller available")
            return

        try:
            # Get process from process_manager
            process_manager = self.process_controller.process_manager
            process = process_manager.get_process(self.process_id)

            if not process:
                logger.error(f"Process {self.process_id} not found")
                QMessageBox.warning(self, "Error", "Proceso no encontrado")
                self.close()
                return

            self.current_process = process

            # Fill form fields
            self.name_input.setText(process.name)
            self.description_input.setText(process.description or "")
            self.icon_input.setText(process.icon or "")
            self.delay_spinbox.setValue(process.delay_between_steps)

            if process.color:
                self.selected_color = process.color
                self.update_color_button()

            # Load steps
            for step in process.steps:
                self.add_step_to_constructor(step)

            logger.info(f"Loaded process for editing: {process.name} with {len(process.steps)} steps")

        except Exception as e:
            logger.error(f"Error loading process for editing: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al cargar proceso: {str(e)}")

    # ==================== ITEM DISPLAY ====================

    def display_items(self):
        """Display filtered items"""
        # Clear existing items
        while self.items_layout.count() > 1:  # Keep stretch
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add filtered items
        for item in self.filtered_items:
            item_btn = ItemButton(item)
            item_btn.setMaximumHeight(60)

            # Double-click to add to process
            item_btn.mouseDoubleClickEvent = lambda event, i=item: self.on_item_double_clicked(i)

            self.items_layout.insertWidget(self.items_layout.count() - 1, item_btn)

        # Update count
        self.items_count_label.setText(f"({len(self.filtered_items)})")

    def on_search_changed(self, query: str):
        """Handle search query change"""
        self.apply_filters()

    def on_filter_changed(self):
        """Handle filter change"""
        self.apply_filters()

    def apply_filters(self):
        """Apply all active filters"""
        filtered = self.available_items.copy()

        # Apply category filter
        selected_category_id = self.category_combo.currentData()
        if selected_category_id is not None:
            filtered = [item for item in filtered if item.category_id == selected_category_id]

        # Apply type filter
        selected_type = self.type_combo.currentData()
        if selected_type is not None:
            filtered = [item for item in filtered if item.type == selected_type]

        # Apply search filter
        search_query = self.items_search.search_input.text().strip().lower()
        if search_query:
            filtered = [item for item in filtered
                       if search_query in item.label.lower() or
                          search_query in (item.content or "").lower()]

        self.filtered_items = filtered
        self.display_items()

    def on_item_double_clicked(self, item):
        """Handle double-click on item to add to process"""
        logger.info(f"Adding item to process: {item.label}")

        # Create ProcessStep from item
        step = ProcessStep(
            item_id=item.id,
            step_order=len(self.step_widgets) + 1,
            item_label=item.label,
            item_content=item.content,
            item_type=item.type,
            item_icon=item.icon,
            item_is_sensitive=item.is_sensitive,
            is_enabled=True
        )

        self.add_step_to_constructor(step)

    # ==================== STEP MANAGEMENT ====================

    def add_step_to_constructor(self, step: ProcessStep):
        """Add a step to the constructor panel"""
        is_first = len(self.step_widgets) == 0
        is_last = True  # Always last when adding

        # Create widget
        step_widget = ProcessStepWidget(step, is_first, is_last)

        # Connect signals
        step_widget.step_edited.connect(self.on_step_edit_requested)
        step_widget.step_deleted.connect(self.on_step_delete_requested)
        step_widget.step_moved_up.connect(self.on_step_move_up)
        step_widget.step_moved_down.connect(self.on_step_move_down)

        # Add to layout
        self.steps_layout.insertWidget(len(self.step_widgets), step_widget)
        self.step_widgets.append(step_widget)

        # Update all step widgets
        self.update_step_widgets()

        logger.debug(f"Step added: {step.get_display_label()}")

    def update_step_widgets(self):
        """Update order and button states for all step widgets"""
        for i, widget in enumerate(self.step_widgets):
            is_first = (i == 0)
            is_last = (i == len(self.step_widgets) - 1)
            widget.update_order(i + 1, is_first, is_last)

        # Update count
        self.steps_count_label.setText(f"({len(self.step_widgets)} steps)")

    def on_step_edit_requested(self, step: ProcessStep):
        """Handle step edit request"""
        logger.info(f"Edit requested for step: {step.get_display_label()}")

        try:
            # Import dialog
            from views.dialogs.process_step_config_dialog import ProcessStepConfigDialog

            # Create and show dialog
            dialog = ProcessStepConfigDialog(step, parent=self)
            dialog.config_saved.connect(lambda s: self.on_step_config_saved(s))

            # Show dialog (modal)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                logger.info(f"Step configuration updated: {step.get_display_label()}")

        except Exception as e:
            logger.error(f"Error opening step config dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al abrir configuracion: {str(e)}")

    def on_step_delete_requested(self, step: ProcessStep):
        """Handle step delete request"""
        reply = QMessageBox.question(
            self,
            "Eliminar Step",
            f"Eliminar step '{step.get_display_label()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Find and remove widget
            for i, widget in enumerate(self.step_widgets):
                if widget.get_step() == step:
                    self.steps_layout.removeWidget(widget)
                    widget.deleteLater()
                    self.step_widgets.pop(i)
                    break

            self.update_step_widgets()
            logger.info(f"Step deleted: {step.get_display_label()}")

    def on_step_config_saved(self, step: ProcessStep):
        """Handle step configuration saved - update widget display"""
        try:
            # Find the widget for this step and update it
            for widget in self.step_widgets:
                if widget.get_step() == step:
                    widget.update_step_data(step)
                    logger.info(f"Widget updated for step: {step.get_display_label()}")
                    break

        except Exception as e:
            logger.error(f"Error updating step widget: {e}", exc_info=True)

    def on_step_move_up(self, step: ProcessStep):
        """Move step up in order"""
        for i, widget in enumerate(self.step_widgets):
            if widget.get_step() == step and i > 0:
                # Swap with previous
                self.step_widgets[i], self.step_widgets[i-1] = self.step_widgets[i-1], self.step_widgets[i]

                # Re-add to layout in new order
                self.rebuild_steps_layout()
                self.update_step_widgets()
                break

    def on_step_move_down(self, step: ProcessStep):
        """Move step down in order"""
        for i, widget in enumerate(self.step_widgets):
            if widget.get_step() == step and i < len(self.step_widgets) - 1:
                # Swap with next
                self.step_widgets[i], self.step_widgets[i+1] = self.step_widgets[i+1], self.step_widgets[i]

                # Re-add to layout in new order
                self.rebuild_steps_layout()
                self.update_step_widgets()
                break

    def rebuild_steps_layout(self):
        """Rebuild steps layout after reordering"""
        # Remove all widgets from layout
        while self.steps_layout.count() > 1:
            item = self.steps_layout.takeAt(0)

        # Re-add in new order
        for widget in self.step_widgets:
            self.steps_layout.insertWidget(self.steps_layout.count() - 1, widget)

    # ==================== COLOR PICKER ====================

    def pick_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.update_color_button()

    def update_color_button(self):
        """Update color button appearance"""
        if self.selected_color:
            self.color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.selected_color};
                    color: white;
                    border: 2px solid #ffffff;
                }}
            """)

    # ==================== SAVE ====================

    def on_save_clicked(self):
        """Handle save button click"""
        # Validate
        if not self.validate_process():
            return

        # Build Process object
        process = self.build_process()

        if not process:
            QMessageBox.warning(self, "Error", "Error al construir proceso")
            return

        # Save via controller
        if not self.process_controller:
            QMessageBox.critical(self, "Error", "ProcessController no disponible")
            return

        try:
            if self.editing_mode:
                # Update existing process
                success, message = self.process_controller.save_process(process)
            else:
                # Create new process
                success, message, process_id = self.process_controller.create_process(process)
                if success:
                    self.process_id = process_id

            if success:
                QMessageBox.information(self, "Exito", message)
                self.process_saved.emit(self.process_id)
                self.close()
            else:
                QMessageBox.warning(self, "Error", message)

        except Exception as e:
            logger.error(f"Error saving process: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    def validate_process(self) -> bool:
        """Validate process data"""
        # Check name
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validacion", "El nombre del proceso es requerido")
            self.name_input.setFocus()
            return False

        # Check steps
        if len(self.step_widgets) == 0:
            QMessageBox.warning(self, "Validacion",
                               "El proceso debe tener al menos 1 step")
            return False

        return True

    def build_process(self) -> Process:
        """Build Process object from form data"""
        try:
            # Create Process
            process = Process(
                id=self.process_id if self.editing_mode else None,
                name=self.name_input.text().strip(),
                description=self.description_input.text().strip() or None,
                icon=self.icon_input.text().strip() or "⚙️",
                color=self.selected_color,
                execution_mode="sequential",
                delay_between_steps=self.delay_spinbox.value()
            )

            # Add steps
            for widget in self.step_widgets:
                step = widget.get_step()
                process.add_step(step)

            return process

        except Exception as e:
            logger.error(f"Error building process: {e}", exc_info=True)
            return None

    # ==================== CLOSE ====================

    def closeEvent(self, event):
        """Handle window close"""
        # Check if there are unsaved changes
        if len(self.step_widgets) > 0:
            reply = QMessageBox.question(
                self,
                "Cerrar",
                "Hay cambios sin guardar. Cerrar de todas formas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        self.window_closed.emit()
        event.accept()

