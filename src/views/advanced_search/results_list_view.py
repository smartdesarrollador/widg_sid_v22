"""
Results List View - Display search results in a scrollable list
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from views.widgets.item_widget import ItemButton
from models.item import Item

import logging
logger = logging.getLogger(__name__)


class ResultsListView(QWidget):
    """
    List view for search results

    Displays results as a vertical list of ItemButton widgets
    """

    # Signal emitted when an item is clicked
    item_clicked = pyqtSignal(object)

    # Signal emitted when URL should be opened in embedded browser
    url_open_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.item_widgets = []

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for results
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        # Container widget for scroll area
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(8)

        # Empty state label
        self.empty_label = QLabel("No hay resultados")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
                padding: 50px;
            }
        """)
        self.scroll_layout.addWidget(self.empty_label)

        # Add stretch to push items to top
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def update_results(self, results):
        """
        Update the list with new results

        Args:
            results: List of result dictionaries from AdvancedSearchEngine
        """
        logger.info(f"Updating list view with {len(results)} results")

        # Clear existing widgets
        self.clear_results()

        self.results = results

        if not results:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)

        # Create ItemButton for each result
        for result in results:
            try:
                # Convert result dict to Item object
                item = Item(
                    item_id=str(result.get('id', '')),
                    label=result.get('label', ''),
                    content=result.get('content', ''),
                    item_type=result.get('type', 'TEXT').lower(),  # Convert to lowercase for ItemType enum
                    description=result.get('description'),
                    tags=result.get('tags', '').split(',') if result.get('tags') else [],
                    is_favorite=bool(result.get('is_favorite', 0)),
                    is_sensitive=bool(result.get('is_sensitive', 0)),
                    is_active=True
                )

                # Add category name as custom attribute for display
                item.category_name = result.get('category_name', 'Sin categoría')
                item.category_icon = result.get('category_icon', '📁')

                # Add date and usage fields from search results
                item.use_count = result.get('use_count', 0)
                item.last_used = result.get('last_used')
                item.created_at = result.get('created_at')

                # Create item widget with category badge
                item_widget = ItemButton(item, show_category=True)
                item_widget.item_clicked.connect(self._on_item_clicked)
                item_widget.url_open_requested.connect(self._on_url_open_requested)

                # Insert before stretch
                self.scroll_layout.insertWidget(
                    self.scroll_layout.count() - 1,
                    item_widget
                )

                self.item_widgets.append(item_widget)

            except Exception as e:
                logger.error(f"Error creating item widget: {e}", exc_info=True)

        logger.debug(f"Created {len(self.item_widgets)} item widgets")

    def clear_results(self):
        """Clear all result widgets"""
        # Remove all item widgets
        for widget in self.item_widgets:
            widget.deleteLater()

        self.item_widgets.clear()
        self.results.clear()

    def _on_item_clicked(self, item):
        """Handle item click"""
        logger.debug(f"Item clicked in list view: {item.label}")
        self.item_clicked.emit(item)

    def _on_url_open_requested(self, url: str):
        """Handle URL open request from ItemButton"""
        logger.info(f"URL open requested in list view: {url}")
        # Forward signal to parent
        self.url_open_requested.emit(url)

    def get_selected_items(self):
        """Get currently selected items (for future multi-select)"""
        # TODO: Implement multi-select support
        return []
