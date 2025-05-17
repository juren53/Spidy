"""
Custom Web View for Spidy Web Browser

This module contains the WebEngineView class which extends QWebEngineView
to provide enhanced features such as mouse wheel zooming and context menus.
"""

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QWheelEvent, QAction
from PyQt6.QtWidgets import QMenu, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QApplication, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
import logging
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
        
        # Set up logging
        self.logger = logging.getLogger('spidy.web_view')
        
        # Apply initial zoom factor
    def createWindow(self, window_type):
        """
        Override createWindow to handle opening links in new tabs.
        
        This method is automatically called when a link needs to be opened in a new 
        window/tab, such as when a user right-clicks on a link and selects "Open Link in New Tab".
        
        Args:
            window_type: The type of window to create
            
        Returns:
            A WebEngineView instance for the new tab
        """
        print(f"RIGHT-CLICK: createWindow called with type {window_type}")
        
        # Find the browser that has a tab_manager
        browser = None
        parent = self.parent()
        
        # Approach 1: Traverse parent hierarchy
        while parent:
            print(f"Checking parent: {parent}")
            if hasattr(parent, 'tab_manager'):
                browser = parent
                break
            parent = parent.parent()
        
        # Approach 2: Look for the browser in top-level widgets
        if not browser:
            from PyQt6.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'tab_manager'):
                    browser = widget
                    print(f"Found browser in top-level widgets: {browser}")
                    break
        
        # If browser is found, use its tab_manager to create a new tab
        if browser:
            print(f"Using browser.tab_manager: {browser.tab_manager}")
            new_tab = browser.tab_manager.add_new_tab()
            print(f"Created new tab: {new_tab}")
            return new_tab
        
        # If all else fails, create a new WebEngineView directly
        print("Could not find browser, creating standalone WebEngineView")
        new_view = WebEngineView()
        return new_view
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
        # Create the standard context menu with all default actions
        menu = self.createStandardContextMenu()
        
        # Find and analyze menu actions
        view_source_text = "View Page Source"
        open_link_text = "Open Link in New Tab"
        copy_link_text = "Copy Link Address"
        existing_actions = menu.actions()
        
        # Check if this is a context menu triggered on a link
        is_link_menu = False
        open_link_action = None
        link_url = None
        
        # First pass: identify menu type and important actions
        for action in existing_actions:
            action_text = action.text()
            
            # Look for link-related menu items to determine if we're on a link
            if action_text in ["Open Link in New Tab", "Open Link in New Window", "Copy Link Address"]:
                is_link_menu = True
                if action_text == open_link_text:
                    open_link_action = action
                
                # Try to get the link URL from the action's data if possible
                action_data = action.data()
                if action_data and isinstance(action_data, QUrl) and action_data.isValid():
                    link_url = action_data
            
            # Find and customize the "View Page Source" action
            if action_text == view_source_text or "source" in action_text.lower():
                try:
                    # Disconnect existing connections if any
                    action.triggered.disconnect()
                except TypeError:
                    # No connections to disconnect
                    pass
                # Connect our custom implementation
                action.triggered.connect(self.view_page_source)
        
        # If we're on a link but couldn't get the URL from action data, try to get it with JavaScript
        if is_link_menu and not link_url:
            # We'll use JavaScript to retrieve the URL and then continue processing
            self.page().runJavaScript(
                "document.activeElement.closest('a') ? document.activeElement.closest('a').href : ''",
                self._handle_context_menu_on_link_with_url(menu, open_link_action, open_link_text, existing_actions, event)
            )
            return  # Exit and let the callback handle the rest
        
        # Second pass: handle the "Open Link in New Tab" action if needed
        if is_link_menu and link_url and link_url.isValid():
            self.logger.debug(f"Context menu on link: {link_url.toString()}")
            
            # If there's no "Open Link in New Tab" action, create our own and add it to the menu
            if not open_link_action:
                open_link_action = QAction(open_link_text, self)
                menu.insertAction(existing_actions[0] if existing_actions else None, open_link_action)
            
            # Make sure "Open Link in New Tab" has a proper connection
            # Disconnect any existing connections to avoid multiple signals
            try:
                open_link_action.triggered.disconnect()
            except TypeError:
                pass
            
            # Use a direct connection with a fixed URL to avoid lambda capture issues
            url_to_open = QUrl(link_url)  # Create a new QUrl instance to avoid reference issues
            self.logger.debug(f"Setting up action to open: {url_to_open.toString()}")
            
            # Connect to our handler with a direct reference to avoid lambda capture issues
            open_link_action.triggered.connect(lambda checked=False, url=url_to_open: self.open_link_in_new_tab(url))
        
        # Add "View Page Source" if it wasn't found
        view_source_action_found = any(action.text() == view_source_text or "source" in action.text().lower() 
                                       for action in existing_actions)
        if not view_source_action_found:
            # Add a separator before our custom actions if needed
            if len(existing_actions) > 0 and not existing_actions[-1].isSeparator():
                menu.addSeparator()
            
            # Add "View Page Source" action
            view_source_action = QAction(view_source_text, self)
            view_source_action.triggered.connect(self.view_page_source)
            menu.addAction(view_source_action)
        
        # Show the menu at the appropriate position
        menu.exec(event.globalPos())
    
    def _handle_context_menu_on_link_with_url(self, menu, open_link_action, open_link_text, existing_actions, original_event):
        """
        Callback to handle context menu on a link after retrieving the URL via JavaScript.
        
        Args:
            menu: The context menu
            open_link_action: The Open Link in New Tab action if it exists
            open_link_text: The text for the Open Link in New Tab action
            existing_actions: All existing actions in the menu
            original_event: The original context menu event
        """
        def callback(href):
            # If we got a valid URL from JavaScript
            if href and isinstance(href, str) and href.strip():
                link_url = QUrl(href)
                if link_url.isValid():
                    self.logger.debug(f"Got link URL from JavaScript: {link_url.toString()}")
                    
                    # If there's no "Open Link in New Tab" action, create our own
                    if not open_link_action:
                        new_action = QAction(open_link_text, self)
                        menu.insertAction(existing_actions[0] if existing_actions else None, new_action)
                        
                        # Create a fixed QUrl to avoid reference issues
                        url_to_open = QUrl(link_url)
                        self.logger.debug(f"Context menu JS - setting up action to open: {url_to_open.toString()}")
                        
                        # Connect with direct reference to avoid lambda capture issues
                        new_action.triggered.connect(lambda checked=False, url=url_to_open: self.open_link_in_new_tab(url))
                    else:
                        # Otherwise update the existing action
                        try:
                            open_link_action.triggered.disconnect()
                        except TypeError:
                            pass
                            
                        # Create a fixed QUrl to avoid reference issues
                        url_to_open = QUrl(link_url)
                        self.logger.debug(f"Context menu JS - updating action to open: {url_to_open.toString()}")
                        
                        # Connect with direct reference to avoid lambda capture issues
                        open_link_action.triggered.connect(lambda checked=False, url=url_to_open: self.open_link_in_new_tab(url))
            
            # Show the menu at the appropriate position
            menu.exec(original_event.globalPos())
        
        return callback
    
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
        
        # Log zoom change using logger
        self.logger.debug(f"Zoom factor set to: {factor:.2f}")
        
        return factor
    
    def get_zoom_factor(self):
        """
        Get the current zoom factor.
        
        Returns:
            float: The current zoom factor
        """
        return self._zoom_factor
    
    def open_link_in_new_tab(self, url):
        """
        Handler for opening a link in a new tab.
        
        This method is called when the user selects "Open Link in New Tab"
        from the context menu. It opens the URL in a new tab using one of
        several approaches, prioritizing the most direct methods.
        
        Args:
            url (QUrl): The URL to open in a new tab
        """
        self.logger.debug(f"RIGHT-CLICK: Opening link in new tab: {url.toString()}")
        
        # Make sure we have a valid URL
        if not url.isValid():
            self.logger.warning(f"Invalid URL: {url.toString()}")
            return False

        # Track whether we succeed in finding the tab manager
        success = False
        
        try:
            # APPROACH 1: Find tab_manager via parent hierarchy without type checking
            self.logger.debug("Trying to find tab_manager through parent hierarchy")
            parent = self
            while parent:
                if hasattr(parent, 'tab_manager'):
                    self.logger.debug("SUCCESS: Found tab_manager in parent hierarchy")
                    parent.tab_manager.add_new_tab(url)
                    return True
                parent = parent.parent()
        
            # APPROACH 2: Look through all top-level widgets for tab_manager
            self.logger.debug("Trying to find tab_manager in top-level widgets")
            for widget in QApplication.topLevelWidgets():
                # First check the widget itself
                if hasattr(widget, 'tab_manager'):
                    self.logger.debug("SUCCESS: Found tab_manager in top-level widget")
                    widget.tab_manager.add_new_tab(url)
                    return True
                
                # If not, try its immediate children
                for child in widget.children():
                    if hasattr(child, 'tab_manager'):
                        self.logger.debug("SUCCESS: Found tab_manager in top-level widget's child")
                        child.tab_manager.add_new_tab(url)
                        return True
        except Exception as e:
            self.logger.error(f"Error while finding tab_manager in widget hierarchy: {e}")

        try:
            # APPROACH 3: Create a new tab directly using tab_manager module
            self.logger.debug("Trying to create new tab via direct import")
            from tab_manager import TabManager
            
            # Find instance via application's top-level widgets again but using instanceof
            for widget in QApplication.topLevelWidgets():
                for child in widget.findChildren(QWidget):
                    if isinstance(child, TabManager):
                        self.logger.debug("SUCCESS: Found TabManager instance via instanceof")
                        child.add_new_tab(url)
                        return True
        except Exception as e:
            self.logger.error(f"Error while trying direct TabManager import: {e}")

        try:
            # APPROACH 4: Use the page's signals if properly connected
            self.logger.debug("Trying page signal approach")
            page = self.page()
            if hasattr(page, 'open_url_in_new_tab'):
                self.logger.debug("Page has open_url_in_new_tab signal, emitting")
                page.open_url_in_new_tab.emit(url)
                return True
            else:
                self.logger.debug("Page does NOT have open_url_in_new_tab signal")
                if hasattr(page, 'link_clicked_new_tab'):
                    self.logger.debug("Page has link_clicked_new_tab signal, emitting")
                    page.link_clicked_new_tab.emit(url.toString(), "_blank")
                    return True
                else:
                    self.logger.debug("Page does NOT have link_clicked_new_tab signal")
        except Exception as e:
            self.logger.error(f"Error with signal emission: {e}")

        # APPROACH 5: Manual navigation using custom JavaScript
        self.logger.warning("All methods failed, attempting JavaScript solution")
        try:
            # Detect if running inside an iframe and break out if needed
            detect_js = """
            (function() {
                // Create a global function to track the tab creation
                window._SPIDY_LAST_TAB_URL = null;
                window._SPIDY_CREATE_NEW_TAB = function(url) {
                    window._SPIDY_LAST_TAB_URL = url;
                    console.log('[Spidy Browser] Creating new tab for: ' + url);
                    var win = window.open(url, '_blank');
                    if (win) {
                        win.opener = null;
                        return true;
                    }
                    return false;
                };
                
                // Return whether successful
                return window._SPIDY_CREATE_NEW_TAB('""" + url.toString() + """');
            })();
            """
            
            # Execute the JavaScript and log the result
            self.page().runJavaScript(detect_js, callback=lambda result: 
                self.logger.debug(f"JavaScript new tab creation result: {result}"))
            
            # Tell the user we've opened the link
            return True
            
        except Exception as e:
            self.logger.error(f"JavaScript approach failed: {e}")
            
        # As an absolute last resort, navigate the current page
        self.logger.error("ALL TAB CREATION METHODS FAILED - navigating current page instead")
        self.load(url)
        return False
