"""
Highlight Delegate for TreeWidget
Custom item delegate that highlights search matches in text
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPalette, QTextDocument, QAbstractTextDocumentLayout, QPainter
import logging

logger = logging.getLogger(__name__)


class HighlightDelegate(QStyledItemDelegate):
    """Custom delegate that highlights search query in item text"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_query = ""
        self.highlight_color = "#8b6914"  # Dark gold/brown highlight for dark theme

    def set_search_query(self, query: str):
        """Set the search query to highlight"""
        self.search_query = query.lower() if query else ""
        logger.debug(f"Highlight delegate search query set to: '{self.search_query}'")

    def paint(self, painter, option, index):
        """Custom paint method to highlight text"""
        if not self.search_query:
            # No search query, use default painting
            super().paint(painter, option, index)
            return

        # Get the text to display
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text or not isinstance(text, str):
            super().paint(painter, option, index)
            return

        # Check if text contains search query
        text_lower = text.lower()
        if self.search_query not in text_lower:
            # No match, use default painting
            super().paint(painter, option, index)
            return

        # Save painter state
        painter.save()

        # Draw background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif index.row() % 2 == 1:
            painter.fillRect(option.rect, option.palette.alternateBase())
        else:
            painter.fillRect(option.rect, option.palette.base())

        # Create HTML with highlighted text
        html_text = self._create_highlighted_html(text, self.search_query)

        # Create text document for rich text rendering
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(html_text)

        # Set text color based on selection state
        if option.state & QStyle.StateFlag.State_Selected:
            text_color = option.palette.color(QPalette.ColorRole.HighlightedText)
        else:
            text_color = option.palette.color(QPalette.ColorRole.Text)

        doc.setDefaultStyleSheet(f"body {{ color: {text_color.name()}; }}")

        # Calculate text position with padding
        text_rect = QRect(option.rect)
        text_rect.setLeft(text_rect.left() + 5)
        text_rect.setTop(text_rect.top() + 2)

        # Translate painter to text position
        painter.translate(text_rect.topLeft())

        # Set clip rect
        clip_rect = QRect(0, 0, text_rect.width(), text_rect.height())
        painter.setClipRect(clip_rect)

        # Draw the text document
        ctx = QAbstractTextDocumentLayout.PaintContext()
        doc.documentLayout().draw(painter, ctx)

        # Restore painter state
        painter.restore()

    def _create_highlighted_html(self, text: str, query: str) -> str:
        """
        Create HTML with highlighted query matches

        Args:
            text: Original text
            query: Search query to highlight

        Returns:
            HTML string with highlighted matches
        """
        if not query:
            return text

        # Escape HTML special characters in text
        text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Find all matches (case-insensitive)
        result = []
        text_lower = text_escaped.lower()
        query_lower = query.lower()

        last_pos = 0
        pos = text_lower.find(query_lower)

        while pos != -1:
            # Add text before match
            result.append(text_escaped[last_pos:pos])

            # Add highlighted match
            match_text = text_escaped[pos:pos + len(query)]
            result.append(f'<span style="background-color: {self.highlight_color}; color: #ffffff; font-weight: bold;">{match_text}</span>')

            last_pos = pos + len(query)
            pos = text_lower.find(query_lower, last_pos)

        # Add remaining text
        result.append(text_escaped[last_pos:])

        return ''.join(result)

    def sizeHint(self, option, index):
        """Return the size hint for the item"""
        # Use default size hint
        return super().sizeHint(option, index)
