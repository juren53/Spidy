"""
Custom Web View for Spidy Web Browser

This module contains the WebEngineView class which extends QWebEngineView
to provide enhanced features such as mouse wheel zooming and context menus.
"""

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QWheelEvent, QAction
from PyQt6.QtWidgets import QMenu, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView

class WebEngineView(QWebEngineView):
    """
    Enhanced WebEngineView with zoom functionality and context menu.
    
    This class extends QWebEngineView to add zoom support via Ctrl+mouse wheel,
    similar to how modern web browsers handle zooming. It also implements a
    context menu with "View Page Source" option.
    """
    
    # Constants for zoom limits and increments
    MIN_ZOOM = 0.25
    MAX_ZOOM = 5.0
    ZOOM_INCREMENT = 0.1
    DEFAULT_ZOOM = 1.0
    
    def __init__(self, parent=None):
        """Initialize the WebEngineView with default zoom factor."""
        super().__init__(parent)
        self._zoom_factor = self.DEFAULT_ZOOM
        
        # Apply initial zoom factor
        self.setZoomFactor(self._zoom_factor)
    
    def wheelEvent(self, event: QWheelEvent):
        """
        Handle wheel events for zooming functionality.
        
        When Ctrl key is pressed and the mouse wheel is scrolled,
        zoom in or out depending on scroll direction.
        
        Args:
            event (QWheelEvent): The wheel event to handle
        """
        # Check if Ctrl key is pressed
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Calculate zoom based on wheel direction
            delta = event.angleDelta().y()
            
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
                
            # Event has been handled
            event.accept()
        else:
            # Call the parent handler for normal scrolling
            super().wheelEvent(event)
    
    def contextMenuEvent(self, event):
        """
        Create a custom context menu with additional browser-specific options.
        
        Args:
            event: The context menu event
        """
        # Create the standard context menu
        menu = self.createStandardContextMenu()
        
        # Add a separator before our custom actions
        menu.addSeparator()
        
        # Add "View Page Source" action
        view_source_action = QAction("View Page Source", self)
        view_source_action.triggered.connect(self.view_page_source)
        menu.addAction(view_source_action)
        
        # Show the menu at the appropriate position
        menu.exec(event.globalPosition().toPoint())
    
    def view_page_source(self):
        """Display the HTML source of the current page in a dialog."""
        # Get the page's HTML
        self.page().toHtml(self._show_source_dialog)
    
    def _show_source_dialog(self, html_source):
        """
        Show a dialog with the page source HTML.
        
        Args:
            html_source (str): The HTML source of the page
        """
        # Create a dialog window
        dialog = QDialog(self)
        dialog.setWindowTitle("Page Source")
        dialog.resize(800, 600)
        
        # Create a layout
        layout = QVBoxLayout(dialog)
        
        # Create a text edit widget for the source code
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(html_source)
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Use a monospace font for better readability of code
        font = text_edit.font()
        font.setFamily("Courier New")
        text_edit.setFont(font)
        
        # Add text edit to the layout
        layout.addWidget(text_edit)
        
        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show the dialog
        dialog.exec()
    
    def zoom_in(self):
        """Increase the zoom factor by one increment, up to maximum zoom."""
        new_zoom = min(self._zoom_factor + self.ZOOM_INCREMENT, self.MAX_ZOOM)
        self.set_zoom_factor(new_zoom)
        return new_zoom
    
    def zoom_out(self):
        """Decrease the zoom factor by one increment, down to minimum zoom."""
        new_zoom = max(self._zoom_factor - self.ZOOM_INCREMENT, self.MIN_ZOOM)
        self.set_zoom_factor(new_zoom)
        return new_zoom
    
    def reset_zoom(self):
        """Reset the zoom factor to the default value (1.0)."""
        self.set_zoom_factor(self.DEFAULT_ZOOM)
        return self.DEFAULT_ZOOM
    
    def set_zoom_factor(self, factor):
        """
        Set the zoom factor and apply it to the page.
        
        Args:
            factor (float): The zoom factor to apply
            
        Returns:
            float: The actual zoom factor after applying limits
        """
        # Apply zoom limits
        factor = max(min(factor, self.MAX_ZOOM), self.MIN_ZOOM)
        
        # Update internal value and apply to view
        self._zoom_factor = factor
        self.setZoomFactor(factor)
        
        # Log zoom change (could be replaced with a signal)
        print(f"Zoom factor set to: {factor:.2f}")
        
        return factor
    
    def get_zoom_factor(self):
        """
        Get the current zoom factor.
        
        Returns:
            float: The current zoom factor
        """
        return self._zoom_factor
