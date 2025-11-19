"""
Category Editor
Widget for editing categories and their items
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox, QInputDialog, QDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
import uuid
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.category import Category
from models.item import Item, ItemType
from views.item_editor_dialog import ItemEditorDialog

logger = logging.getLogger(__name__)


class CategoryEditor(QWidget):
    """
    Category and item editor widget
    Two-column layout with categories list and items list
    """

    # Signal emitted when data changes
    data_changed = pyqtSignal()

    def __init__(self, controller=None, parent=None):
        """
        Initialize category editor

        Args:
            controller: MainController instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.controller = controller
        self.categories = []
        self.current_category = None

        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        # Set background color
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
        """)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Left column - Categories
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        # Categories label
        categories_label = QLabel("Categorías")
        categories_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        left_layout.addWidget(categories_label)

        # Search box for categories
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar categoría...")
        self.search_input.textChanged.connect(self.filter_categories)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        left_layout.addWidget(self.search_input)

        # Categories list
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(200)
        self.categories_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.categories_list.itemSelectionChanged.connect(self.on_category_selected)
        self.categories_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        left_layout.addWidget(self.categories_list)

        # Category buttons
        cat_buttons_layout = QHBoxLayout()
        cat_buttons_layout.setSpacing(5)

        self.add_cat_button = QPushButton("+")
        self.add_cat_button.setFixedSize(40, 30)
        self.add_cat_button.setToolTip("Agregar categoría")
        self.add_cat_button.clicked.connect(self.add_category)

        self.delete_cat_button = QPushButton("-")
        self.delete_cat_button.setFixedSize(40, 30)
        self.delete_cat_button.setToolTip("Eliminar categoría")
        self.delete_cat_button.clicked.connect(self.delete_category)
        self.delete_cat_button.setEnabled(False)

        cat_buttons_layout.addWidget(self.add_cat_button)
        cat_buttons_layout.addWidget(self.delete_cat_button)
        cat_buttons_layout.addStretch()

        left_layout.addLayout(cat_buttons_layout)

        main_layout.addLayout(left_layout)

        # Right column - Items
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Items label
        self.items_label = QLabel("Items")
        self.items_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        right_layout.addWidget(self.items_label)

        # Search box for items
        self.items_search_input = QLineEdit()
        self.items_search_input.setPlaceholderText("🔍 Buscar item...")
        self.items_search_input.textChanged.connect(self.filter_items)
        self.items_search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        right_layout.addWidget(self.items_search_input)

        # Items list
        self.items_list = QListWidget()
        self.items_list.setMinimumWidth(280)
        self.items_list.itemSelectionChanged.connect(self.on_item_selected)
        self.items_list.itemDoubleClicked.connect(lambda: self.edit_item())
        self.items_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        right_layout.addWidget(self.items_list)

        # Item buttons
        item_buttons_layout = QHBoxLayout()
        item_buttons_layout.setSpacing(5)

        self.add_item_button = QPushButton("+")
        self.add_item_button.setFixedSize(40, 30)
        self.add_item_button.setToolTip("Agregar item")
        self.add_item_button.clicked.connect(self.add_item)
        self.add_item_button.setEnabled(False)

        # Botón de creación masiva
        self.bulk_add_button = QPushButton("📝")
        self.bulk_add_button.setFixedSize(40, 30)
        self.bulk_add_button.setToolTip("Crear múltiples items de forma rápida")
        self.bulk_add_button.clicked.connect(self.create_bulk_items)
        self.bulk_add_button.setEnabled(False)

        self.edit_item_button = QPushButton("✎")
        self.edit_item_button.setFixedSize(40, 30)
        self.edit_item_button.setToolTip("Editar item")
        self.edit_item_button.clicked.connect(self.edit_item)
        self.edit_item_button.setEnabled(False)

        self.delete_item_button = QPushButton("-")
        self.delete_item_button.setFixedSize(40, 30)
        self.delete_item_button.setToolTip("Eliminar item")
        self.delete_item_button.clicked.connect(self.delete_item)
        self.delete_item_button.setEnabled(False)

        item_buttons_layout.addWidget(self.add_item_button)
        item_buttons_layout.addWidget(self.bulk_add_button)
        item_buttons_layout.addWidget(self.edit_item_button)
        item_buttons_layout.addWidget(self.delete_item_button)
        item_buttons_layout.addStretch()

        right_layout.addLayout(item_buttons_layout)

        main_layout.addLayout(right_layout)

        # Apply button styles
        button_style = """
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #007acc;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #555555;
                border: 1px solid #2d2d2d;
            }
        """
        self.add_cat_button.setStyleSheet(button_style)
        self.delete_cat_button.setStyleSheet(button_style)
        self.add_item_button.setStyleSheet(button_style)
        self.bulk_add_button.setStyleSheet(button_style)
        self.edit_item_button.setStyleSheet(button_style)
        self.delete_item_button.setStyleSheet(button_style)

    def load_categories(self):
        """Load categories from controller"""
        import traceback
        logger.warning(f"[LOAD_CATEGORIES] ⚠️ CALLED! This will OVERWRITE self.categories")
        logger.warning(f"[LOAD_CATEGORIES] Called from:")
        logger.warning(f"[LOAD_CATEGORIES] {''.join(traceback.format_stack()[-3:-1])}")
        logger.warning(f"[LOAD_CATEGORIES] Current categories in memory: {len(self.categories)}")

        if not self.controller:
            return

        # IMPORTANT: Always load directly from config_manager to get ALL categories with ALL items
        # Do NOT use controller.get_categories() because it might return filtered categories
        # without items loaded (from CategoryFilterEngine)
        if hasattr(self.controller, 'config_manager'):
            # Clear cache to force fresh reload from database
            self.controller.config_manager._categories_cache = None

            # Load ALL categories with ALL items directly from database
            self.categories = self.controller.config_manager.get_categories()
            logger.info(f"[LOAD_CATEGORIES] ✅ Loaded {len(self.categories)} categories from database")
            for cat in self.categories:
                logger.debug(f"  - {cat.name}: {len(cat.items)} items")
        else:
            # Fallback to controller (shouldn't happen)
            self.categories = self.controller.get_categories()

        self.refresh_categories_list()

    def refresh_categories_list(self):
        """Refresh the categories list widget"""
        self.categories_list.clear()

        for category in self.categories:
            item = QListWidgetItem(f"{category.name} ({len(category.items)})")
            item.setData(Qt.ItemDataRole.UserRole, category)
            self.categories_list.addItem(item)

        # Reapply filter if search text exists
        if hasattr(self, 'search_input') and self.search_input.text():
            self.filter_categories(self.search_input.text())

    def filter_categories(self, text):
        """Filter categories list based on search text"""
        search_text = text.lower().strip()

        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            category = item.data(Qt.ItemDataRole.UserRole)

            # Check if search text matches category name
            if search_text in category.name.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def filter_items(self, text):
        """Filter items list based on search text"""
        search_text = text.lower().strip()

        for i in range(self.items_list.count()):
            list_item = self.items_list.item(i)
            item = list_item.data(Qt.ItemDataRole.UserRole)

            # Search in item label and content
            matches = (
                search_text in item.label.lower() or
                search_text in item.content.lower()
            )

            if matches:
                list_item.setHidden(False)
            else:
                list_item.setHidden(True)

    def on_category_selected(self):
        """Handle category selection"""
        selected_items = self.categories_list.selectedItems()

        if not selected_items:
            self.current_category = None
            self.items_list.clear()
            self.items_label.setText("Items")
            self.delete_cat_button.setEnabled(False)
            self.add_item_button.setEnabled(False)
            self.bulk_add_button.setEnabled(False)
            return

        # Get selected category
        item = selected_items[0]
        self.current_category = item.data(Qt.ItemDataRole.UserRole)

        # Update items list
        self.refresh_items_list()

        # Update label
        self.items_label.setText(f"Items - {self.current_category.name}")

        # Enable buttons
        self.delete_cat_button.setEnabled(True)
        self.add_item_button.setEnabled(True)
        self.bulk_add_button.setEnabled(True)

    def refresh_items_list(self):
        """Refresh the items list for current category"""
        self.items_list.clear()

        if not self.current_category:
            # Clear search when no category selected
            if hasattr(self, 'items_search_input'):
                self.items_search_input.clear()
            return

        for item in self.current_category.items:
            list_item = QListWidgetItem(f"{item.label}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.items_list.addItem(list_item)

        # Reapply filter if search text exists
        if hasattr(self, 'items_search_input') and self.items_search_input.text():
            self.filter_items(self.items_search_input.text())

    def on_item_selected(self):
        """Handle item selection"""
        selected = len(self.items_list.selectedItems()) > 0
        self.edit_item_button.setEnabled(selected)
        self.delete_item_button.setEnabled(selected)

    def add_category(self):
        """Add new category - saves directly to database"""
        name, ok = QInputDialog.getText(
            self,
            "Nueva Categoría",
            "Nombre de la categoría:"
        )

        if not ok or not name.strip():
            logger.info("[ADD_CATEGORY] Dialog cancelled or empty name")
            return

        try:
            logger.info(f"[ADD_CATEGORY] Creating new category: {name.strip()}")

            # Save directly to database to get real ID
            category_id = self.controller.config_manager.db.add_category(
                name=name.strip(),
                icon="📁",  # Default icon
                is_predefined=False
            )

            if not category_id:
                logger.error("[ADD_CATEGORY] Failed to create category in database")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo crear la categoría '{name.strip()}' en la base de datos."
                )
                return

            logger.info(f"[ADD_CATEGORY] Category created in database with ID: {category_id}")

            # Reload categories from database to get the new one with real ID
            self.load_categories()

            # Select the newly created category
            for i in range(self.categories_list.count()):
                item = self.categories_list.item(i)
                category = item.data(Qt.ItemDataRole.UserRole)
                if category and category.id == category_id:
                    self.categories_list.setCurrentItem(item)
                    logger.info(f"[ADD_CATEGORY] New category selected in UI")
                    break

            # Show success message
            QMessageBox.information(
                self,
                "Éxito",
                f"La categoría '{name.strip()}' se creó correctamente.\n\n"
                f"ID: {category_id}\n"
                f"Ahora puedes agregar items a esta categoría."
            )

            # Invalidate filter cache
            if hasattr(self.controller, 'invalidate_filter_cache'):
                self.controller.invalidate_filter_cache()

            self.data_changed.emit()
            logger.info("[ADD_CATEGORY] Category creation completed successfully")

        except Exception as e:
            logger.error(f"[ADD_CATEGORY] Error creating category: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear la categoría:\n{str(e)}"
            )

    def delete_category(self):
        """Delete selected category"""
        if not self.current_category:
            return

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Eliminar Categoría",
            f"¿Eliminar la categoría '{self.current_category.name}' y todos sus items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.categories.remove(self.current_category)
            self.current_category = None
            self.refresh_categories_list()
            self.items_list.clear()
            self.data_changed.emit()

    def add_item(self):
        """Add new item to current category"""
        if not self.current_category:
            logger.warning("[ADD_ITEM] No current category selected")
            return

        logger.info(f"[ADD_ITEM] Adding item to category: {self.current_category.name} (ID: {self.current_category.id})")

        # Convert category_id to integer (needed for database FOREIGN KEY)
        try:
            category_id_int = int(self.current_category.id) if str(self.current_category.id).isdigit() else None
        except (ValueError, TypeError):
            category_id_int = None

        if not category_id_int:
            logger.error(f"[ADD_ITEM] Invalid category_id: {self.current_category.id}")
            QMessageBox.critical(
                self,
                "Error",
                f"ID de categoría inválido: {self.current_category.id}\n\n"
                "La categoría debe tener un ID numérico válido en la base de datos."
            )
            return

        # Open dialog with controller and category_id - saving happens in the dialog
        dialog = ItemEditorDialog(
            category_id=category_id_int,
            controller=self.controller,
            parent=self
        )

        # Conectar señales para actualizar UI automáticamente
        if self.controller and hasattr(self.controller, 'refresh_ui'):
            dialog.item_created.connect(lambda cat_id: self.controller.refresh_ui())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Item was saved successfully in the dialog
            # Save the current category ID before reloading
            current_category_id = self.current_category.id if self.current_category else None

            # Reload the category from database to get updated items
            logger.info(f"[ADD_ITEM] Item saved, reloading category data from database")
            self.load_categories()

            # Re-select the current category by ID
            if current_category_id:
                for i in range(self.categories_list.count()):
                    item = self.categories_list.item(i)
                    category = item.data(Qt.ItemDataRole.UserRole)
                    if category and category.id == current_category_id:
                        self.categories_list.setCurrentItem(item)
                        break

            self.data_changed.emit()
            self.refresh_categories_list()  # Update count
            self.data_changed.emit()
        else:
            logger.info("[ADD_ITEM] Dialog was cancelled")

    def create_bulk_items(self):
        """Crear múltiples items de forma masiva"""
        if not self.current_category:
            QMessageBox.warning(
                self,
                "Error",
                "Selecciona una categoría primero"
            )
            logger.warning("[BULK_CREATE] No current category selected")
            return

        # Guardar referencia a la categoría antes de refrescar listas
        # (refresh_categories_list() limpia la selección)
        category = self.current_category
        logger.info(f"[BULK_CREATE] Opening bulk dialog for category: {category.name}")

        # Importar el diálogo
        from views.dialogs.bulk_item_dialog import BulkItemDialog

        # Abrir diálogo de creación masiva
        db_path = str(self.controller.config_manager.db.db_path) if self.controller and hasattr(self.controller, 'config_manager') and hasattr(self.controller.config_manager, 'db') else None
        dialog = BulkItemDialog(category.name, db_path, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            items_data = dialog.get_items_data()
            selected_color = dialog.get_selected_color()  # Obtener color seleccionado

            if not items_data:
                QMessageBox.information(
                    self,
                    "Información",
                    "No se ingresaron items"
                )
                logger.info("[BULK_CREATE] No items entered, dialog accepted but no data")
                return

            # Crear items
            created_count = 0
            for item_data in items_data:
                item_id = f"item_{uuid.uuid4().hex[:8]}"
                item = Item(
                    item_id=item_id,
                    label=item_data["label"],
                    content=item_data["label"],  # Mismo valor para label y content
                    item_type=ItemType.TEXT,  # Tipo fijo TEXT
                    tags=item_data["tags"],
                    description="",  # Vacío por defecto
                    is_sensitive=False,  # Por defecto no es sensible
                    icon=None,
                    color=selected_color,  # Asignar color seleccionado
                    is_active=True,  # Por defecto activo
                    is_archived=False  # Por defecto no archivado
                )
                category.items.append(item)
                created_count += 1
                logger.debug(f"[BULK_CREATE] Created item: '{item.label}' with ID: {item_id}, color: {selected_color}")

            # Refresh UI
            self.refresh_items_list()
            self.refresh_categories_list()  # Update count
            self.data_changed.emit()

            # Notificación de éxito
            QMessageBox.information(
                self,
                "Éxito",
                f"✅ Se crearon {created_count} items exitosamente\n\n"
                f"Puedes editarlos individualmente si necesitas cambiar el tipo, "
                f"agregar descripción o modificar el contenido."
            )

            logger.info(f"[BULK_CREATE] Successfully created {created_count} items in category '{category.name}'")
        else:
            logger.info("[BULK_CREATE] Dialog cancelled by user")

    def edit_item(self):
        """Edit selected item"""
        selected_items = self.items_list.selectedItems()
        if not selected_items or not self.current_category:
            return

        # Get selected item
        list_item = selected_items[0]
        item = list_item.data(Qt.ItemDataRole.UserRole)

        # Convert category_id to integer (needed for database FOREIGN KEY)
        try:
            category_id_int = int(self.current_category.id) if str(self.current_category.id).isdigit() else None
        except (ValueError, TypeError):
            category_id_int = None

        if not category_id_int:
            logger.error(f"[EDIT_ITEM] Invalid category_id: {self.current_category.id}")
            QMessageBox.critical(
                self,
                "Error",
                f"ID de categoría inválido: {self.current_category.id}\n\n"
                "La categoría debe tener un ID numérico válido en la base de datos."
            )
            return

        # Open dialog with item and controller - saving happens in the dialog
        dialog = ItemEditorDialog(
            item=item,
            category_id=category_id_int,
            controller=self.controller,
            parent=self
        )

        # Conectar señales para actualizar UI automáticamente
        if self.controller and hasattr(self.controller, 'refresh_ui'):
            dialog.item_updated.connect(lambda item_id, cat_id: self.controller.refresh_ui())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Item was updated successfully in the dialog
            # Save the current category ID before reloading
            current_category_id = self.current_category.id if self.current_category else None

            # Reload the category from database to get updated items
            logger.info(f"[EDIT_ITEM] Item updated, reloading category data from database")
            self.load_categories()

            # Re-select the current category by ID
            if current_category_id:
                for i in range(self.categories_list.count()):
                    cat_item = self.categories_list.item(i)
                    category = cat_item.data(Qt.ItemDataRole.UserRole)
                    if category and category.id == current_category_id:
                        self.categories_list.setCurrentItem(cat_item)
                        break

            self.data_changed.emit()

    def delete_item(self):
        """Delete selected item"""
        selected_items = self.items_list.selectedItems()
        if not selected_items or not self.current_category:
            return

        # Get selected item
        list_item = selected_items[0]
        item = list_item.data(Qt.ItemDataRole.UserRole)

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Eliminar Item",
            f"¿Eliminar el item '{item.label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_category.remove_item(item.id)
            self.refresh_items_list()
            self.refresh_categories_list()  # Update count
            self.data_changed.emit()

    def get_categories(self):
        """
        Get current categories list

        Returns:
            List of categories
        """
        import traceback
        logger.info(f"[GET_CATEGORIES] Called from:")
        logger.info(f"[GET_CATEGORIES] {''.join(traceback.format_stack()[-3:-1])}")
        logger.info(f"[GET_CATEGORIES] Returning {len(self.categories)} categories")
        for i, cat in enumerate(self.categories):
            logger.info(f"[GET_CATEGORIES]   {i+1}. {cat.name} (ID: {cat.id}) - {len(cat.items)} items")
            # Only log items for new categories (custom_ prefix)
            if cat.id.startswith('custom_'):
                for j, item in enumerate(cat.items):
                    logger.info(f"[GET_CATEGORIES]      Item {j+1}: {item.label}")
        return self.categories
