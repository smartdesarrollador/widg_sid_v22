"""
Organization Settings
Widget for Tag Groups and Smart Collections management
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from views.dialogs.tag_groups_dialog import TagGroupsDialog
from views.dialogs.smart_collections_dialog import SmartCollectionsDialog

logger = logging.getLogger(__name__)


class OrganizationSettings(QWidget):
    """
    Organization settings widget
    Manage Tag Groups and Smart Collections
    """

    # Signal emitted when settings change
    settings_changed = pyqtSignal()

    def __init__(self, config_manager=None, parent=None):
        """
        Initialize organization settings

        Args:
            config_manager: ConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager

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
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_label = QLabel("🗂️ Organización de Items")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        main_layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "Gestiona plantillas de tags y filtros inteligentes para organizar tus items de forma eficiente."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #a0a0a0; font-size: 10pt; margin-bottom: 10px;")
        main_layout.addWidget(desc_label)

        # Tag Groups group
        tag_groups_group = QGroupBox("🏷️ Grupos de Tags")
        tag_groups_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        tag_groups_layout = QVBoxLayout()
        tag_groups_layout.setSpacing(10)

        # Description
        tag_groups_desc = QLabel(
            "Gestiona plantillas de tags reutilizables para organizar tus items"
        )
        tag_groups_desc.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        tag_groups_desc.setWordWrap(True)
        tag_groups_layout.addWidget(tag_groups_desc)

        # Features list
        features_label = QLabel(
            "• Crea plantillas con tags predefinidos\n"
            "• Aplica grupos al crear items\n"
            "• Mantén consistencia en tus tags\n"
            "• Iconos y colores personalizados"
        )
        features_label.setStyleSheet("color: #cccccc; font-size: 9pt; margin-left: 10px;")
        tag_groups_layout.addWidget(features_label)

        # Button to open Tag Groups manager
        manage_tag_groups_btn = QPushButton("📋 Gestionar Grupos de Tags")
        manage_tag_groups_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        manage_tag_groups_btn.clicked.connect(self.open_tag_groups_dialog)
        tag_groups_layout.addWidget(manage_tag_groups_btn)

        tag_groups_group.setLayout(tag_groups_layout)
        main_layout.addWidget(tag_groups_group)

        # Smart Collections group
        smart_collections_group = QGroupBox("🔍 Colecciones Inteligentes")
        smart_collections_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        smart_collections_layout = QVBoxLayout()
        smart_collections_layout.setSpacing(10)

        # Description
        smart_collections_desc = QLabel(
            "Crea filtros guardados que se actualizan automáticamente con los items que coinciden"
        )
        smart_collections_desc.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        smart_collections_desc.setWordWrap(True)
        smart_collections_layout.addWidget(smart_collections_desc)

        # Features list
        collections_features = QLabel(
            "• Filtros dinámicos por tags, tipo, categoría\n"
            "• Actualización automática de resultados\n"
            "• Búsquedas guardadas reutilizables\n"
            "• Filtros complejos con múltiples criterios"
        )
        collections_features.setStyleSheet("color: #cccccc; font-size: 9pt; margin-left: 10px;")
        smart_collections_layout.addWidget(collections_features)

        # Button to open Smart Collections manager
        manage_smart_collections_btn = QPushButton("📋 Gestionar Colecciones Inteligentes")
        manage_smart_collections_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        manage_smart_collections_btn.clicked.connect(self.open_smart_collections_dialog)
        smart_collections_layout.addWidget(manage_smart_collections_btn)

        smart_collections_group.setLayout(smart_collections_layout)
        main_layout.addWidget(smart_collections_group)

        # Info box
        info_group = QGroupBox("💡 ¿Cómo usar estas herramientas?")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QVBoxLayout()

        info_text = QLabel(
            "<b>Tag Groups:</b> Crea plantillas de tags para aplicar al crear items.<br>"
            "Ejemplo: Grupo 'Python' con tags: python, fastapi, api<br><br>"
            "<b>Smart Collections:</b> Guarda búsquedas para encontrar items rápidamente.<br>"
            "Ejemplo: Colección 'APIs Python' filtra items con tags python+api"
        )
        info_text.setStyleSheet("color: #cccccc; font-size: 9pt;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Spacer
        main_layout.addStretch()

    def open_tag_groups_dialog(self):
        """Abrir el diálogo de gestión de Tag Groups"""
        try:
            logger.debug("Opening Tag Groups dialog")
            dialog = TagGroupsDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening Tag Groups dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el gestor de Tag Groups:\n{str(e)}"
            )

    def open_smart_collections_dialog(self):
        """Abrir el diálogo de gestión de Smart Collections"""
        try:
            logger.debug("Opening Smart Collections dialog")
            dialog = SmartCollectionsDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening Smart Collections dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el gestor de Colecciones Inteligentes:\n{str(e)}"
            )
