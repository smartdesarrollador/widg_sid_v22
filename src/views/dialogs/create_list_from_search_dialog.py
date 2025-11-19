"""
Diálogo para crear lista desde búsqueda global
Permite seleccionar categoría destino y configurar la lista
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QComboBox, QListWidget,
                             QListWidgetItem, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class CreateListFromSearchDialog(QDialog):
    """Diálogo para crear lista desde búsqueda global"""

    # Señal emitida cuando se crea la lista: (list_name, category_id, item_ids)
    list_created = pyqtSignal(str, int, list)

    def __init__(self, items, db_manager, config_manager, list_controller, parent=None):
        super().__init__(parent)
        self.items = items
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.list_controller = list_controller

        self.init_ui()

    def init_ui(self):
        """Inicializar UI del diálogo"""
        self.setWindowTitle("Crear Lista desde Búsqueda")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        # No cerrar app al cerrar diálogo
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("📋 Crear Lista Avanzada")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Nombre de la lista
        name_group = QGroupBox("Nombre de la Lista")
        name_layout = QVBoxLayout(name_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Comandos Git Útiles")
        name_layout.addWidget(self.name_input)

        layout.addWidget(name_group)

        # Selección de categoría
        category_group = QGroupBox("Categoría Destino")
        category_layout = QVBoxLayout(category_group)

        self.category_combo = QComboBox()
        self.load_categories()
        category_layout.addWidget(self.category_combo)

        layout.addWidget(category_group)

        # Items a incluir
        items_group = QGroupBox(f"Items a Incluir ({len(self.items)} items)")
        items_layout = QVBoxLayout(items_group)

        # Checkbox para seleccionar todos
        self.select_all_checkbox = QCheckBox("Seleccionar todos")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        items_layout.addWidget(self.select_all_checkbox)

        # Lista de items
        self.items_list = QListWidget()
        for item in self.items:
            category_info = f"[{item.category_name}]" if hasattr(item, 'category_name') else ""
            list_item = QListWidgetItem(f"{category_info} {item.label}")
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            list_item.setCheckState(Qt.CheckState.Checked)
            self.items_list.addItem(list_item)

        items_layout.addWidget(self.items_list)
        layout.addWidget(items_group)

        # Botones
        buttons_layout = QHBoxLayout()

        create_btn = QPushButton("✅ Crear Lista")
        create_btn.clicked.connect(self.create_list)
        buttons_layout.addWidget(create_btn)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        # Estilos
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #00aaff;
            }
            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #00aaff;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #007acc;
            }
            QCheckBox {
                color: #e0e0e0;
            }
        """)

    def load_categories(self):
        """Cargar categorías disponibles"""
        # Agregar opción inicial sin selección
        self.category_combo.addItem("-- Selecciona una categoría --", None)

        if not self.db_manager:
            return

        # Obtener categorías desde DBManager
        categories = self.db_manager.get_categories(include_inactive=False)
        for category in categories:
            self.category_combo.addItem(
                f"{category['icon']} {category['name']}",
                category['id']
            )

    def toggle_select_all(self, state):
        """Seleccionar/deseleccionar todos los items"""
        check_state = Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            item.setCheckState(check_state)

    def create_list(self):
        """Crear la lista con los items seleccionados"""
        # Validar nombre
        list_name = self.name_input.text().strip()
        if not list_name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Debes proporcionar un nombre para la lista")
            return

        # Obtener categoría seleccionada
        category_id = self.category_combo.currentData()
        if not category_id:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Debes seleccionar una categoría")
            return

        # Obtener items seleccionados
        selected_item_ids = []
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                item_id = item.data(Qt.ItemDataRole.UserRole)
                selected_item_ids.append(item_id)

        if not selected_item_ids:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Debes seleccionar al menos un item")
            return

        # Crear lista usando ListController
        try:
            self.list_controller.create_list_from_items(
                list_name=list_name,
                category_id=int(category_id),
                item_ids=[int(id) for id in selected_item_ids]
            )

            # Emitir señal
            self.list_created.emit(list_name, int(category_id), [int(id) for id in selected_item_ids])

            # Cerrar diálogo
            self.accept()

        except Exception as e:
            logger.error(f"Error creating list: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Error al crear lista: {e}")
