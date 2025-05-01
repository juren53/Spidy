import sys
import os
import json
import time
import urllib.parse
from datetime import datetime

# First import Qt core attributes that must be set before QApplication is created
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

# Set Qt attributes in correct order BEFORE initializing QtWebEngine or QApplication
# These attributes must be set on QCoreApplication before any UI components are created
QtCore.QCoreApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)  # Prevents QQuickWidget warnings
QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)  # Disables high DPI scaling
QtCore.QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)  # Enables sharing of OpenGL contexts
QtCore.QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)  # Use software OpenGL if available

# Initialize QtWebEngine before importing QtWebEngineWidgets
from PyQt5.QtWebEngine import QtWebEngine
QtWebEngine.initialize()

# Import QtWebEngineWidgets BEFORE creating QApplication instance
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

# Import QApplication and create instance
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

# Now import remaining QtCore modules
from PyQt5.QtCore import QUrl, QDateTime, QSize
from PyQt5.QtGui import QKeySequence, QIcon

# Import remaining widget modules
from PyQt5.QtWidgets import (QLineEdit, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QMenuBar, QMenu, QAction, QMainWindow,
                            QDialog, QTableWidget, QTableWidgetItem, QHeaderView, 
                            QDialogButtonBox, QFileDialog, QMessageBox,
                            QLabel, QGridLayout, QTabWidget, QTabBar, QShortcut)


class LinkHandler(QWebEnginePage):
    # Define navigation type names for readable logs
    NAV_TYPE_NAMES = {
        QWebEnginePage.NavigationTypeLinkClicked: "Link Click",
        QWebEnginePage.NavigationTypeFormSubmitted: "Form Submission",
        QWebEnginePage.NavigationTypeBackForward: "Back/Forward Navigation",
        QWebEnginePage.NavigationTypeReload: "Page Reload",
        QWebEnginePage.NavigationTypeRedirect: "Redirect",
        QWebEnginePage.NavigationTypeTyped: "URL Typed",
        QWebEnginePage.NavigationTypeOther: "Other Navigation"
    }
    
    # Define supported URL schemes with handling policies
    SUPPORTED_SCHEMES = {
        'http': {'allow': True, 'description': 'HTTP protocol'},
        'https': {'allow': True, 'description': 'Secure HTTP protocol'},
        'file': {'allow': True, 'description': 'Local file access'},
        'ftp': {'allow': True, 'description': 'File Transfer Protocol'},
        'ftps': {'allow': True, 'description': 'Secure File Transfer Protocol'},
        'data': {'allow': True, 'description': 'Data URI scheme'},
        'mailto': {'allow': True, 'description': 'Email address link', 'external': True},
        'tel': {'allow': True, 'description': 'Telephone number link', 'external': True},
        'about': {'allow': True, 'description': 'Browser information'},
    }
    
    # Define potentially dangerous schemes
    SUSPICIOUS_SCHEMES = ['javascript', 'vbscript', 'data']

    def __init__(self, parent=None):
        super().__init__(parent)
        # Create profile that allows local file access
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        # Enable ALL required settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        
        # Initialize navigation history tracking
        self.nav_history = []
        self.nav_success_count = 0
        self.nav_failure_count = 0
        self.current_nav_start_time = 0
        self.suspicious_navigation_attempts = 0
        
    def log_navigation(self, message, level="INFO"):
        """Log navigation events with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")

    def get_navigation_type_name(self, nav_type):
        """Get readable name for navigation type"""
        return self.NAV_TYPE_NAMES.get(nav_type, f"Unknown ({nav_type})")
    
    def is_suspicious_url(self, url):
        """Check if URL might be suspicious or malicious"""
        suspicious = False
        reasons = []
        
        # Check scheme
        scheme = url.scheme().lower()
        if scheme in self.SUSPICIOUS_SCHEMES:
            suspicious = True
            reasons.append(f"Suspicious scheme: {scheme}")
            
        # Check for unusual characters in hostname
        host = url.host()
        if '@' in host or '%' in host:
            suspicious = True
            reasons.append(f"Suspicious characters in hostname: {host}")
            
        # Check for very long URLs (potential obfuscation)
        if len(url.toString()) > 2000:
            suspicious = True
            reasons.append(f"Excessively long URL: {len(url.toString())} chars")
        
        return suspicious, reasons
    
    def record_navigation_attempt(self, url, nav_type, is_main_frame, success, error_reason=None):
        """Record a navigation attempt in the history"""
        end_time = time.time()
        duration = round((end_time - self.current_nav_start_time) * 1000, 2) if self.current_nav_start_time > 0 else 0
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url.toString(),
            "type": nav_type,
            "type_name": self.get_navigation_type_name(nav_type),
            "is_main_frame": is_main_frame,
            "scheme": url.scheme(),
            "success": success,
            "duration_ms": duration
        }
        
        if error_reason:
            entry["error"] = error_reason
            
        self.nav_history.append(entry)
        
        # Update counters
        if success:
            self.nav_success_count += 1
        else:
            self.nav_failure_count += 1
            
        # Keep history at a reasonable size
        if len(self.nav_history) > 100:
            self.nav_history = self.nav_history[-100:]
            
        return entry
    
    def get_navigation_stats(self):
        """Get statistics about navigation history"""
        total = self.nav_success_count + self.nav_failure_count
        success_rate = (self.nav_success_count / total * 100) if total > 0 else 0
        
        # Calculate average duration for successful navigations
        durations = [entry.get('duration_ms', 0) for entry in self.nav_history 
                    if entry.get('success', False) and entry.get('duration_ms', 0) > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_navigations": total,
            "successful": self.nav_success_count,
            "failed": self.nav_failure_count,
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "suspicious_attempts": self.suspicious_navigation_attempts
        }
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        """Enhanced navigation request handler with improved logging and security checks"""
        # Record start time for performance tracking
        self.current_nav_start_time = time.time()
        
        # Get navigation type name for readable logs
        nav_type_name = self.get_navigation_type_name(nav_type)
        
        # Enhanced structured debug logging
        self.log_navigation("\nNavigation Request Details:", "DEBUG")
        self.log_navigation(f"URL: {url.toString()}", "DEBUG")
        self.log_navigation(f"Type: {nav_type} ({nav_type_name})", "DEBUG")
        self.log_navigation(f"Is Main Frame: {is_main_frame}", "DEBUG")
        self.log_navigation(f"URL Scheme: {url.scheme()}", "DEBUG")
        
        # URL security check
        is_suspicious, reasons = self.is_suspicious_url(url)
        if is_suspicious:
            self.suspicious_navigation_attempts += 1
            self.log_navigation(f"SECURITY WARNING: Potentially suspicious URL detected:", "WARNING")
            for reason in reasons:
                self.log_navigation(f"- {reason}", "WARNING")
        
        # Always allow main frame navigation
        if is_main_frame:
            self.log_navigation(f"Allowing main frame navigation to {url.toString()}", "INFO")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True)
            return True
            
        # Handle navigation by type
        scheme = url.scheme().lower()
        
        # Handle different navigation types
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            self.log_navigation(f"Link clicked: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeFormSubmitted:
            self.log_navigation(f"Form submitted to: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeBackForward:
            self.log_navigation(f"Back/Forward navigation to: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeReload:
            self.log_navigation(f"Page reload: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeRedirect:
            self.log_navigation(f"Redirect to: {url.toString()}", "INFO")
            
        # Process URL based on scheme
        if scheme in self.SUPPORTED_SCHEMES:
            scheme_info = self.SUPPORTED_SCHEMES[scheme]
            
            # Check if scheme is allowed
            if not scheme_info.get('allow', False):
                self.log_navigation(f"Navigation blocked - scheme '{scheme}' is not allowed", "WARNING")
                self.record_navigation_attempt(url, nav_type, is_main_frame, False, 
                                             f"Scheme '{scheme}' is not allowed")
                return False
                
            # Handle external schemes (mailto, tel, etc.)
            if scheme_info.get('external', False):
                self.log_navigation(f"External scheme '{scheme}' detected, attempting to open with external application", "INFO")
                # For mailto and tel links, you might integrate with system applications
                # This is a simplified demonstration - in production, you might use QDesktopServices
                self.record_navigation_attempt(url, nav_type, is_main_frame, True, "Handled by external application")
                return False  # Don't navigate in browser, but consider it successful for tracking

            # Handle specific schemes
            if scheme == 'file':
                path = url.toLocalFile()
                self.log_navigation(f"Handling file URL: {path}", "DEBUG")
                
                # Handle relative paths
                if not os.path.isabs(path):
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    path = os.path.join(base_dir, path)
                    self.log_navigation(f"Converted to absolute path: {path}", "DEBUG")
                
                if os.path.exists(path):
                    self.log_navigation(f"File exists, allowing navigation", "INFO")
                    self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                    return True
                    
                # File doesn't exist - try fallback
                self.log_navigation(f"File does not exist: {path}", "WARNING")
                # Try fallback to HTTP if file not found
                http_url = QUrl("http://" + url.fileName())
                if http_url.isValid():
                    self.log_navigation(f"Attempting fallback to HTTP: {http_url.toString()}", "INFO")
                    self.record_navigation_attempt(url, nav_type, is_main_frame, True, "File not found, falling back to HTTP")
                    return True
                
                # No fallback available
                self.log_navigation(f"Navigation failed - file not found and no valid fallback", "ERROR")
                self.record_navigation_attempt(url, nav_type, is_main_frame, False, "File not found and no valid fallback")
                return False
                
            # Standard HTTP/HTTPS handling
            elif scheme in ('http', 'https'):
                self.log_navigation(f"Allowing navigation to {scheme} URL: {url.toString()}", "INFO")
                self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                return True
                
            # FTP handling
            elif scheme in ('ftp', 'ftps'):
                self.log_navigation(f"Allowing navigation to {scheme} URL: {url.toString()}", "INFO")
                self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                return True
                
            # Data URI scheme (inline content)
            elif scheme == 'data':
                self.log_navigation(f"Processing data URI", "INFO")
                # Check if it's a potentially malicious data URI (e.g., executable content)
                data_content = url.toString()
                if 'application/x-msdownload' in data_content or 'application/octet-stream' in data_content:
                    self.log_navigation("Potentially unsafe data URI with executable content", "WARNING")
                    self.suspicious_navigation_attempts += 1
                
                self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                return True
                
            # Default handling for supported schemes
            self.log_navigation(f"Allowing navigation to {scheme} URL via default handler", "INFO")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True)
            return True
                
        else:
            # Unsupported scheme
            self.log_navigation(f"Unsupported URL scheme: {scheme}", "WARNING")
            
            # If it's a known but unsupported scheme, log specifically
            if scheme in ['javascript', 'vbscript']:
                self.log_navigation(f"Script scheme '{scheme}' not supported for security reasons", "WARNING")
                self.record_navigation_attempt(url, nav_type, is_main_frame, False, f"Script scheme '{scheme}' blocked")
                return False
                
            # Unknown scheme - try anyway but log the attempt
            self.log_navigation(f"Unknown scheme '{scheme}', attempting navigation with caution", "WARNING")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True, f"Unknown scheme '{scheme}' allowed with caution")
            return True

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Log JavaScript messages for debugging
        print(f"JavaScript ({level}) [{sourceID}:{lineNumber}]: {message}")

    def javaScriptAlert(self, securityOrigin, msg):
        """Handle JavaScript alerts with enhanced logging"""
        self.log_navigation(f"JavaScript Alert from {securityOrigin.host()}: {msg}", "INFO")
        # In a real implementation, you might show a dialog to the user
        # For headless operation, we just log the alert
        
    def javaScriptConfirm(self, securityOrigin, msg):
        """Handle JavaScript confirmation dialogs with enhanced logging"""
        self.log_navigation(f"JavaScript Confirm from {securityOrigin.host()}: {msg}", "INFO")
        # In a real implementation, you would show a dialog and return the user's choice
        # For headless operation, we default to accepting all confirms
        return True
        
    def javaScriptPrompt(self, securityOrigin, msg, defaultValue, result):
        """Handle JavaScript prompt dialogs with enhanced logging"""
        self.log_navigation(f"JavaScript Prompt from {securityOrigin.host()}: {msg} (default: {defaultValue})", "INFO")
        # In a real implementation, you would show a dialog and set result to the user's input
        # For headless operation, we default to returning the default value
        result.clear()
        result.append(defaultValue)
        return True
        
    def certificateError(self, error):
        """Handle SSL certificate errors with enhanced logging"""
        self.log_navigation(f"SSL Certificate Error: {error.errorDescription()}", "ERROR")
        self.log_navigation(f"URL with certificate error: {error.url().toString()}", "ERROR")
        
        # Record the navigation failure
        self.record_navigation_attempt(
            error.url(), 
            QWebEnginePage.NavigationTypeOther,  # We don't know the type here
            True,  # Assuming main frame
            False,  # Navigation failed
            f"SSL Certificate Error: {error.errorDescription()}"
        )
        
        # In a real application, you might allow the user to bypass the error in some cases
        # For this sample, we reject all certificate errors for security
        return False
    def createWindow(self, windowType):
        """Handle window creation requests with enhanced logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        window_type_name = {
            QWebEnginePage.WebBrowserWindow: "Browser Window",
            QWebEnginePage.WebBrowserTab: "Browser Tab",
            QWebEnginePage.WebDialog: "Web Dialog",
            QWebEnginePage.WebBrowserBackgroundTab: "Background Tab"
        }.get(windowType, f"Unknown ({windowType})")
        
        self.log_navigation(f"Window creation requested: {window_type_name}", "INFO")
        
        # Create a new page for pop-ups or new windows
        new_page = LinkHandler(self.parent())
        
        # You could integrate with a tab system here
        # For demo purposes, we're just returning the new page
        # Return the new page we created
        return new_page
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Disable GPU acceleration and WebGL to prevent errors
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        # Configure profile for handling link targets
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        # Initialize tab-related variables
        self.tabs = []
        self.tab_widgets = []

        # Initialize history and bookmarks lists and config file paths
        self.history = []
        self.bookmarks = []
        self.config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        self.history_file = os.path.join(self.config_dir, 'history.json')
        self.bookmarks_file = os.path.join(self.config_dir, 'bookmarks.json')
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Load history and bookmarks from files
        self.load_history()
        self.load_bookmarks()
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Simple Web Browser')
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        # Create application menu
        self.create_menu()
        
        # Create the tab widget to hold multiple browser tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        
        # Setup the navigation bar (will be placed above the tabs)
        self.setup_navigation_bar()
        
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(self.nav_layout)
        layout.addWidget(self.tab_widget)
        
        # Set layout for central widget
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)
        
        # Add tab button to tab bar
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(QSize(24, 24))
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)
        
        # Create a new tab to start with
        self.add_new_tab(QUrl('https://search.brave.com/'))
        
        # Add keyboard shortcuts for tab management
        QShortcut(QKeySequence("Ctrl+T"), self, self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.previous_tab)
        
        self.show()
    
    def keyPressEvent(self, event):
        current_view = self.current_view()
        if not current_view:
            super().keyPressEvent(event)
            return
            
        # Handle Left Arrow key for back navigation
        if event.key() == Qt.Key_Left and current_view.page().history().canGoBack():
            self.view_back()
        # Handle Right Arrow key for forward navigation
        elif event.key() == Qt.Key_Right and current_view.page().history().canGoForward():
            self.view_forward()
        # Let the parent class handle other key events
        else:
            super().keyPressEvent(event)
    
    # Tab Management Methods
    def setup_navigation_bar(self):
        """Setup the navigation bar with URL field and buttons"""
        self.url_field = QLineEdit()
        self.back_button = QPushButton('Back')
        self.forward_button = QPushButton('Forward')
        self.go_button = QPushButton('Go')
        self.reload_button = QPushButton('Reload')
        
        # Connect navigation buttons
        self.go_button.clicked.connect(self.navigate_to_url)
        self.back_button.clicked.connect(self.view_back)
        self.forward_button.clicked.connect(self.view_forward)
        self.reload_button.clicked.connect(self.reload_page)
        self.url_field.returnPressed.connect(self.navigate_to_url)
        
        # Initialize with disabled navigation buttons
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        
        # Create horizontal layout for navigation controls
        self.nav_layout = QHBoxLayout()
        self.nav_layout.addWidget(self.back_button)
        self.nav_layout.addWidget(self.forward_button)
        self.nav_layout.addWidget(self.reload_button)
        self.nav_layout.addWidget(self.url_field)
        self.nav_layout.addWidget(self.go_button)
    
    def add_new_tab(self, qurl=None):
        """Add a new browser tab"""
        if qurl is None or isinstance(qurl, bool):  # Handle both None and boolean cases
            qurl = QUrl('https://search.brave.com/')
        elif isinstance(qurl, str):  # Handle string URLs
            if not qurl.startswith(('http://', 'https://', 'file://')):
                if os.path.exists(qurl):
                    qurl = QUrl.fromLocalFile(os.path.abspath(qurl))
                else:
                    qurl = QUrl('http://' + qurl)
            else:
                qurl = QUrl(qurl)
        # QUrl objects are handled as-is
            
        # Create browser view with custom page handler
        browser = QWebEngineView()
        page = LinkHandler(browser)
        browser.setPage(page)
        
        # Configure settings
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        
        # Add navigation signal connections
        browser.page().linkHovered.connect(lambda url: print(f"Link hovered: {url}"))
        browser.page().featurePermissionRequested.connect(
            lambda securityOrigin, feature: print(f"Permission requested: {feature} from {securityOrigin.host()}")
        )
        
        # Add debug logging
        browser.loadStarted.connect(lambda: print("Page load started"))
        browser.loadProgress.connect(lambda p: print(f"Load progress: {p}%"))
        browser.loadFinished.connect(lambda ok: print(f"Load finished: {'success' if ok else 'failed'}"))
        
        browser.setUrl(qurl)
        
        # Setup connections for the new tab
        browser.urlChanged.connect(lambda qurl, b=browser: self.update_url_field(qurl, b))
        browser.loadFinished.connect(lambda _, b=browser: self.update_tab_title(b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(b))
        
        # Add browser to tabs list
        self.tabs.append(browser)
        
        # Add widget to tab widget
        tab_index = self.tab_widget.addTab(browser, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Connect signals for history tracking and navigation buttons
        browser.loadFinished.connect(lambda ok: self.add_to_history(ok, browser))
        browser.titleChanged.connect(lambda title: self.update_history_title(title, browser))
        browser.loadFinished.connect(lambda: self.update_navigation_buttons())
        browser.urlChanged.connect(lambda: self.update_navigation_buttons())
        
        # Update the URL field
        self.update_url_field(qurl)
        
        return browser
    
    def close_tab(self, index):
        """Close the tab at the given index"""
        # Only allow closing if we have more than one tab
        if self.tab_widget.count() > 1:
            # Remove the tab
            self.tab_widget.removeTab(index)
            
            # Remove the browser from the tabs list
            browser = self.tabs.pop(index)
            
            # Clean up the browser
            browser.deleteLater()
    
    def close_current_tab(self):
        """Close the currently active tab"""
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)
    
    def tab_changed(self, index):
        """Handle tab change events"""
        if index >= 0 and self.tabs:
            # Update the URL field with the current tab's URL
            qurl = self.tabs[index].url()
            self.update_url_field(qurl)
            
            # Update navigation buttons based on the current tab
            self.update_navigation_buttons()
    
    def next_tab(self):
        """Switch to the next tab"""
        current = self.tab_widget.currentIndex()
        if current < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current + 1)
        else:
            # Wrap around to the first tab
            self.tab_widget.setCurrentIndex(0)
    
    def previous_tab(self):
        """Switch to the previous tab"""
        current = self.tab_widget.currentIndex()
        if current > 0:
            self.tab_widget.setCurrentIndex(current - 1)
        else:
            # Wrap around to the last tab
            self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
    
    def current_view(self):
        """Get the current active WebView"""
        return self.tab_widget.currentWidget()

    # Update navigation methods to use current_view
    def view_back(self):
        """Navigate back in current tab"""
        if self.current_view():
            self.current_view().back()

    def view_forward(self):
        """Navigate forward in current tab"""
        if self.current_view():
            self.current_view().forward()

    def reload_page(self):
        """Reload current tab"""
        if self.current_view():
            self.current_view().reload()

    def navigate_to_url(self):
        """Navigate to URL in current tab"""
        url = self.url_field.text()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        if self.current_view():
            self.current_view().setUrl(QUrl(url))

    def update_url_field(self, url, browser=None):
        """Update URL field when tab URL changes"""
        if not browser or browser == self.current_view():
            self.url_field.setText(url.toString())

    def update_navigation_buttons(self):
        """Update navigation button states for current tab"""
        if self.current_view():
            self.back_button.setEnabled(self.current_view().page().history().canGoBack())
            self.forward_button.setEnabled(self.current_view().page().history().canGoForward())

    def update_tab_title(self, browser):
        """Update tab title when page title changes"""
        index = self.tab_widget.indexOf(browser)
        if index != -1:
            title = browser.page().title()
            if title:
                self.tab_widget.setTabText(index, title[:20] + '...' if len(title) > 20 else title)
            else:
                self.tab_widget.setTabText(index, 'New Tab')

    def add_to_history(self, success, browser=None):
        """Add current page to history when loaded successfully"""
        if success and (not browser or browser == self.current_view()):
            current_url = self.current_view().url().toString()
            if current_url and current_url != "about:blank":
                if not self.history or self.history[0].get('url') != current_url:
                    self.history.insert(0, {
                        'url': current_url,
                        'title': self.current_view().title() or current_url,
                        'timestamp': datetime.now().isoformat(),
                        'visited': 1
                    })
                    self.save_history()

    def update_history_title(self, title, browser=None):
        """Update title of current page in history if it exists"""
        if not browser or browser == self.current_view():
            if self.history:
                current_url = self.current_view().url().toString()
                if self.history[0].get('url') == current_url:
                    self.history[0]['title'] = title
                    self.save_history()
    def create_menu(self):
        # Use QMainWindow's built-in menuBar method
        menu_bar = self.menuBar()
        
        # Create menus
        file_menu = menu_bar.addMenu("&File")
        bookmarks_menu = menu_bar.addMenu("&Bookmarks")
        history_menu = menu_bar.addMenu("&History")
        stats_menu = menu_bar.addMenu("&Statistics")
        help_menu = menu_bar.addMenu("Hel&p")
        about_menu = menu_bar.addMenu("&About")
        
        # Add actions to File menu
        save_page_action = QAction("Save Page", self)
        file_menu.addAction(save_page_action)
        save_page_action.triggered.connect(self.save_page)
        
        # Add a separator and Exit action
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        file_menu.addAction(exit_action)
        exit_action.triggered.connect(QApplication.quit)
        
        # Add actions to Bookmarks menu
        add_bookmark_action = QAction("Add Bookmark", self)
        view_bookmarks_action = QAction("View Bookmarks", self)
        clear_bookmarks_action = QAction("Clear Bookmarks", self)
        bookmarks_menu.addAction(add_bookmark_action)
        bookmarks_menu.addAction(view_bookmarks_action)
        bookmarks_menu.addAction(clear_bookmarks_action)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        view_bookmarks_action.triggered.connect(self.view_bookmarks)
        clear_bookmarks_action.triggered.connect(self.clear_bookmarks)
        
        # Add actions to History menu
        view_history_action = QAction("View History", self)
        clear_history_action = QAction("Clear History", self)
        history_menu.addAction(view_history_action)
        history_menu.addAction(clear_history_action)
        view_history_action.triggered.connect(self.view_history)
        clear_history_action.triggered.connect(self.clear_history)
        
        # Add actions to Statistics menu
        view_stats_action = QAction("View Statistics", self)
        stats_menu.addAction(view_stats_action)
        view_stats_action.triggered.connect(self.view_statistics)
        
        # Add actions to Help menu
        help_content_action = QAction("Help Contents", self)
        help_menu.addAction(help_content_action)
        help_content_action.triggered.connect(self.show_help)
        
        # Add actions to About menu
        about_action = QAction("About Spidy", self)
        about_menu.addAction(about_action)
        about_action.triggered.connect(self.show_about)
    
    # History management methods
    def load_history(self):
        """Load browser history from config file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []
    
    def save_history(self):
        """Save browser history to config file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    # These methods are replaced by the updated versions above
    
    # Bookmarks management methods
    def load_bookmarks(self):
        """Load bookmarks from config file"""
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = []
    
    def save_bookmarks(self):
        """Save bookmarks to config file"""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def add_bookmark(self):
        """Add current page to bookmarks"""
        if not self.current_view():
            return
            
        current_url = self.current_view().url().toString()
        title = self.current_view().title() or current_url
        
        # Only add non-empty URLs
        if current_url and current_url != "about:blank":
            # Check if this URL is already bookmarked
            for bookmark in self.bookmarks:
                if bookmark.get('url') == current_url:
                    QMessageBox.information(self, "Bookmark Exists", 
                                           f"'{title}' is already bookmarked.")
                    return
            
            # Add to bookmarks list
            self.bookmarks.append({
                'url': current_url,
                'title': title,
                'added': datetime.now().isoformat()
            })
            
            # Save bookmarks
            self.save_bookmarks()
            QMessageBox.information(self, "Bookmark Added", 
                                   f"'{title}' has been added to your bookmarks.")
    
    def create_bookmarks_dialog(self):
        """Create and return a dialog displaying the bookmarks"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bookmarks")
        dialog.resize(600, 400)
        
        # Create table for bookmark items
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Title", "URL"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Fill table with bookmark items
        table.setRowCount(len(self.bookmarks))
        for i, bookmark in enumerate(self.bookmarks):
            table.setItem(i, 0, QTableWidgetItem(bookmark.get('title', '')))
            table.setItem(i, 1, QTableWidgetItem(bookmark.get('url', '')))
        
        # Double-click on a bookmark item loads that URL
        table.cellDoubleClicked.connect(lambda row, column: 
                                       self.navigate_to_bookmark(self.bookmarks[row]))
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(table)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        
        # Add a Remove button
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(lambda: self.remove_bookmark(table))
        
        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(remove_button)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        return dialog
    
    def navigate_to_bookmark(self, bookmark):
        """Navigate to a URL from bookmarks"""
        if bookmark and 'url' in bookmark and self.current_view():
            self.url_field.setText(bookmark['url'])
            self.current_view().setUrl(QUrl(bookmark['url']))
    
    def remove_bookmark(self, table):
        """Remove selected bookmark from the list"""
        selected_rows = sorted(set(index.row() for index in table.selectedIndexes()), reverse=True)
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a bookmark to remove.")
            return
        
        # Add confirmation dialog
        msg = "Are you sure you want to remove this bookmark?" if len(selected_rows) == 1 else f"Are you sure you want to remove {len(selected_rows)} bookmarks?"
        reply = QMessageBox.question(self, "Confirm Deletion", msg, QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for row in selected_rows:
                if 0 <= row < len(self.bookmarks):
                    title = self.bookmarks[row].get('title', 'Bookmark')
                    del self.bookmarks[row]
                    
            # Update the table
            table.setRowCount(len(self.bookmarks))
            for i, bookmark in enumerate(self.bookmarks):
                table.setItem(i, 0, QTableWidgetItem(bookmark.get('title', '')))
                table.setItem(i, 1, QTableWidgetItem(bookmark.get('url', '')))
                
            # Save bookmarks
            self.save_bookmarks()
            
            # Inform user
            if len(selected_rows) == 1:
                QMessageBox.information(self, "Bookmark Removed", f"'{title}' has been removed from your bookmarks.")
            else:
                QMessageBox.information(self, "Bookmarks Removed", f"{len(selected_rows)} bookmarks have been removed.")
        
    
    def view_bookmarks(self):
        """Show the bookmarks dialog"""
        dialog = self.create_bookmarks_dialog()
        dialog.exec_()
        
    def clear_bookmarks(self):
        """Clear all bookmarks"""
        if not self.bookmarks:
            QMessageBox.information(self, "No Bookmarks", 
                                   "There are no bookmarks to clear.")
            return
            
        reply = QMessageBox.question(self, "Clear Bookmarks", 
                                     "Are you sure you want to clear all bookmarks?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.bookmarks = []
            self.save_bookmarks()
            QMessageBox.information(self, "Bookmarks Cleared", 
                                   "All bookmarks have been cleared.")
    
    # History dialog for displaying history
    def create_history_dialog(self):
        """Create and return a dialog displaying the browser history"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Browsing History")
        dialog.resize(600, 400)
        
        # Create table for history items
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Title", "URL", "Date/Time"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Fill table with history items
        table.setRowCount(len(self.history))
        for i, entry in enumerate(self.history):
            # Convert ISO timestamp to readable format
            try:
                timestamp = datetime.fromisoformat(entry.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = "Unknown"
                
            table.setItem(i, 0, QTableWidgetItem(entry.get('title', '')))
            table.setItem(i, 1, QTableWidgetItem(entry.get('url', '')))
            table.setItem(i, 2, QTableWidgetItem(timestamp))
        
        # Double-click on a history item loads that URL
        table.cellDoubleClicked.connect(lambda row, column: 
                                        self.navigate_to_history_item(self.history[row]))
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(table)
        
        # Add Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        return dialog
    
    def navigate_to_history_item(self, history_item):
        """Navigate to a URL from history"""
        if history_item and 'url' in history_item and self.current_view():
            self.url_field.setText(history_item['url'])
            self.current_view().setUrl(QUrl(history_item['url']))
    
    # Menu action implementations
    def view_history(self):
        """Show the history dialog"""
        dialog = self.create_history_dialog()
        dialog.exec_()
        
    def clear_history(self):
        """Clear browser history"""
        if not self.history:
            QMessageBox.information(self, "No History", 
                                   "There is no browsing history to clear.")
            return
            
        reply = QMessageBox.question(self, "Clear History", 
                                    "Are you sure you want to clear all browsing history?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.history = []
            self.save_history()
            QMessageBox.information(self, "History Cleared", 
                                  "All browsing history has been cleared.")
            print("History cleared")
    
    def create_statistics_dialog(self, stats):
        """Create a dialog displaying the webpage statistics"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Page Statistics")
        dialog.resize(500, 400)
        
        # Create layout for statistics
        layout = QGridLayout()
        
        # Add page information
        layout.addWidget(QLabel("<b>Page Information</b>"), 0, 0, 1, 2)
        
        row = 1
        # Page basic info
        layout.addWidget(QLabel("Title:"), row, 0)
        layout.addWidget(QLabel(stats.get('title', 'N/A')), row, 1)
        
        row += 1
        layout.addWidget(QLabel("URL:"), row, 0)
        layout.addWidget(QLabel(stats.get('url', 'N/A')), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Domain:"), row, 0)
        layout.addWidget(QLabel(stats.get('domain', 'N/A')), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Protocol:"), row, 0)
        layout.addWidget(QLabel(stats.get('protocol', 'N/A')), row, 1)
        
        # Page size
        row += 1
        layout.addWidget(QLabel("<b>Page Size & Elements</b>"), row, 0, 1, 2)
        
        row += 1
        page_size = stats.get('pageSize', 0)
        # Convert to KB if size is large enough
        if page_size > 1024:
            size_text = f"{page_size / 1024:.2f} KB ({page_size} bytes)"
        else:
            size_text = f"{page_size} bytes"
        layout.addWidget(QLabel("Page Size:"), row, 0)
        layout.addWidget(QLabel(size_text), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Links:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('numLinks', 0))), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Images:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('numImages', 0))), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Scripts:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('numScripts', 0))), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Stylesheets:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('numStylesheets', 0))), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Forms:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('numForms', 0))), row, 1)
        
        row += 1
        layout.addWidget(QLabel("Input Fields:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('numInputs', 0))), row, 1)
        
        # Meta information
        row += 1
        layout.addWidget(QLabel("<b>Meta Information</b>"), row, 0, 1, 2)
        
        row += 1
        layout.addWidget(QLabel("Meta Tags:"), row, 0)
        layout.addWidget(QLabel(str(stats.get('metaTags', 0))), row, 1)
        
        if stats.get('description'):
            row += 1
            layout.addWidget(QLabel("Description:"), row, 0)
            layout.addWidget(QLabel(stats.get('description', '')[:100] + ('...' if len(stats.get('description', '')) > 100 else '')), row, 1)
        
        if stats.get('keywords'):
            row += 1
            layout.addWidget(QLabel("Keywords:"), row, 0)
            layout.addWidget(QLabel(stats.get('keywords', '')[:100] + ('...' if len(stats.get('keywords', '')) > 100 else '')), row, 1)
        
        # Timing information
        row += 1
        layout.addWidget(QLabel("<b>Other Information</b>"), row, 0, 1, 2)
        
        row += 1
        layout.addWidget(QLabel("Current Time:"), row, 0)
        layout.addWidget(QLabel(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')), row, 1)
        
        # Add some spacing
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(20)
        
        # Create dialog layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        
        # Add Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        main_layout.addWidget(button_box)
        
        dialog.setLayout(main_layout)
        return dialog
    
    def view_statistics(self):
        """Show statistics about the current webpage"""
        def on_stats_ready(stats):
            dialog = self.create_statistics_dialog(stats)
            dialog.exec_()

        try:
            # Call the collect_page_statistics method directly on the instance
            self.collect_page_statistics(on_stats_ready)
        except Exception as e:
            print(f"Error collecting page statistics: {str(e)}")
            # Create a fallback dialog with error information
            stats = {
                'title': 'Error',
                'url': self.current_view().url().toString() if self.current_view() else 'Unknown',
                'domain': self.current_view().url().host() if self.current_view() else 'Unknown',
                'protocol': self.current_view().url().scheme() if self.current_view() else 'Unknown',
                'error': f'Failed to collect page statistics: {str(e)}'
            }
            on_stats_ready(stats)
        
    def collect_page_statistics(self, callback):
        """Collect statistics about the current webpage using JavaScript"""
        if not self.current_view():
            # No page loaded, return empty stats
            callback({
                'title': 'No page loaded',
                'url': '',
                'domain': '',
                'protocol': '',
                'pageSize': 0,
                'numLinks': 0,
                'numImages': 0,
                'numScripts': 0,
                'numStylesheets': 0,
                'numForms': 0,
                'numInputs': 0,
                'metaTags': 0,
                'description': '',
                'keywords': ''
            })
            return
            
        # JavaScript to collect page statistics
        js_code = """
        (function() {
            try {
                // Basic page info
                var stats = {
                    title: document.title || '',
                    url: window.location.href || '',
                    domain: window.location.hostname || '',
                    protocol: window.location.protocol || '',
                    pageSize: document.documentElement ? document.documentElement.outerHTML.length : 0,
                    numLinks: document.getElementsByTagName('a').length || 0,
                    numImages: document.getElementsByTagName('img').length || 0,
                    numScripts: document.getElementsByTagName('script').length || 0,
                    numStylesheets: 0,
                    numForms: document.getElementsByTagName('form').length || 0,
                    numInputs: document.getElementsByTagName('input').length || 0,
                    metaTags: document.getElementsByTagName('meta').length || 0,
                    description: '',
                    keywords: '',
                    loadTime: 0,
                    domReadyTime: 0,
                    firstPaint: 0
                };
                
                // Count stylesheets properly (HTMLCollection doesn't have filter)
                var links = document.getElementsByTagName('link');
                var stylesheetCount = 0;
                for (var i = 0; i < links.length; i++) {
                    if (links[i].rel && links[i].rel.toLowerCase() === 'stylesheet') {
                        stylesheetCount++;
                    }
                }
                stats.numStylesheets = stylesheetCount;
                
                // Get meta description and keywords if they exist
                var metaDesc = document.querySelector('meta[name="description"]');
                var metaKeywords = document.querySelector('meta[name="keywords"]');
                
                if (metaDesc && metaDesc.getAttribute) {
                    stats.description = metaDesc.getAttribute('content') || '';
                }
                
                if (metaKeywords && metaKeywords.getAttribute) {
                    stats.keywords = metaKeywords.getAttribute('content') || '';
                }
                
                // Try to get performance timing info if available
                if (window.performance && window.performance.timing) {
                    try {
                        var timing = window.performance.timing;
                        if (timing.loadEventEnd && timing.navigationStart) {
                            stats.loadTime = timing.loadEventEnd - timing.navigationStart;
                        }
                        if (timing.domContentLoadedEventEnd && timing.navigationStart) {
                            stats.domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
                        }
                        if (timing.responseEnd && timing.navigationStart) {
                            stats.firstPaint = timing.responseEnd - timing.navigationStart;
                        }
                    } catch (timingError) {
                        console.log('Error accessing performance timing: ' + timingError.message);
                    }
                }
                
                return stats;
            } catch (error) {
                // Return error information if something goes wrong
                return {
                    error: error.message || 'Unknown error occurred',
                    stack: error.stack || '',
                    title: document.title || '',
                    url: window.location.href || ''
                };
            }
        })();
        """
        
        try:
            # Execute JavaScript asynchronously to collect statistics
            # Use the wrap_callback method directly on the instance
            wrapped_callback = self.wrap_callback(callback)
            self.current_view().page().runJavaScript(js_code, wrapped_callback)
        except Exception as e:
            print(f"Error executing JavaScript: {str(e)}")
            callback({
                'title': 'Error',
                'url': self.current_view().url().toString() if self.current_view() else 'Unknown',
                'error': f"Failed to execute JavaScript: {str(e)}"
            })
    def wrap_callback(self, callback):
        """Wrapper for JavaScript callback to handle data properly"""
        def handle_js_data(data):
            try:
                # Create a fallback data dictionary for error cases
                fallback_data = {
                    'title': self.current_view().title() if self.current_view() else 'Unknown',
                    'url': self.current_view().url().toString() if self.current_view() else 'Unknown',
                    'domain': self.current_view().url().host() if self.current_view() else 'Unknown',
                    'protocol': self.current_view().url().scheme() if self.current_view() else 'Unknown',
                    'pageSize': 'Unable to retrieve',
                    'numLinks': 'Unable to retrieve',
                    'numImages': 'Unable to retrieve',
                    'numScripts': 'Unable to retrieve',
                    'numStylesheets': 'Unable to retrieve',
                    'numForms': 'Unable to retrieve', 
                    'numInputs': 'Unable to retrieve',
                    'metaTags': 'Unable to retrieve',
                    'description': 'Unable to retrieve',
                    'keywords': 'Unable to retrieve'
                }
                
                if isinstance(data, dict):
                    # Check if there's an error in the JS response
                    if 'error' in data:
                        print(f"JavaScript error: {data['error']}")
                        # Merge the error with fallback data
                        fallback_data.update(data)
                        callback(fallback_data)
                        return
                    
                    # Process valid data
                    processed_data = {}
                    for key, value in data.items():
                        # Convert None values to readable text
                        processed_data[key] = "Not available" if value is None else value
                    callback(processed_data)
                else:
                    # If data is not a dict, use fallback with whatever we received
                    print(f"Unexpected data format from JavaScript: {type(data)}")
                    fallback_data['js_response'] = str(data)
                    callback(fallback_data)
            except Exception as e:
                # Catch any exceptions in the callback handling
                print(f"Error in JavaScript callback handler: {str(e)}")
                callback({
                    'title': 'Error',
                    'url': self.current_view().url().toString() if self.current_view() else 'Unknown',
                    'error': f"Failed to process page statistics: {str(e)}"
                })
        
        # Return the inner function
        return handle_js_data
    
    def create_help_dialog(self):
        """Create a dialog displaying help contents for the browser"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Spidy Help")
        dialog.resize(600, 500)
        
        # Create layout for help content
        layout = QVBoxLayout()
        
        # Add help content
        layout.addWidget(QLabel("<h2>Spidy Browser Help</h2>"))
        layout.addWidget(QLabel("<p>Welcome to Spidy, an open-source web browser built with Python and PyQt5!</p>"))
        
        # Navigation section
        layout.addWidget(QLabel("<h3>Navigation</h3>"))
        help_text = """
        <p><b>Address Bar:</b> Enter a URL and press Enter or click Go to navigate to a webpage.</p>
        <p><b>Back/Forward:</b> Use the Back and Forward buttons to navigate through your browsing history.</p>
        """
        layout.addWidget(QLabel(help_text))
        
        # Tab Management
        layout.addWidget(QLabel("<h3>Tab Management</h3>"))
        tab_text = """
        <p>Spidy currently supports single-tab browsing. Future versions will include:</p>
        <ul>
          <li>Opening new tabs</li>
          <li>Closing tabs</li>
          <li>Switching between tabs</li>
        </ul>
        """
        layout.addWidget(QLabel(tab_text))
        
        # Saving Pages
        layout.addWidget(QLabel("<h3>Saving Pages</h3>"))
        save_text = """
        <p>To save the current webpage:</p>
        <ol>
          <li>Click on <b>File</b> in the menu bar</li>
          <li>Select <b>Save Page</b></li>
          <li>Choose a location and filename</li>
          <li>Click <b>Save</b></li>
        </ol>
        <p>The page will be saved as an HTML file that you can open later.</p>
        """
        layout.addWidget(QLabel(save_text))
        
        # Bookmarks
        layout.addWidget(QLabel("<h3>Bookmarks</h3>"))
        bookmarks_text = """
        <p>Spidy allows you to bookmark your favorite webpages for quick access later:</p>
        <ul>
          <li><b>Add Bookmark:</b> Click on <b>Bookmarks</b> → <b>Add Bookmark</b> to save the current page.</li>
          <li><b>View Bookmarks:</b> Click on <b>Bookmarks</b> → <b>View Bookmarks</b> to see all your saved bookmarks.</li>
          <li><b>Navigate to a Bookmark:</b> Double-click on any bookmark in the dialog to visit that page.</li>
          <li><b>Remove Bookmark:</b> Select a bookmark in the View Bookmarks dialog and click <b>Remove Selected</b>.</li>
          <li><b>Clear Bookmarks:</b> Click on <b>Bookmarks</b> → <b>Clear Bookmarks</b> to delete all bookmarks.</li>
        </ul>
        """
        layout.addWidget(QLabel(bookmarks_text))
        
        # History
        layout.addWidget(QLabel("<h3>Browsing History</h3>"))
        history_text = """
        <p>Spidy keeps track of your browsing history. To view or manage your history:</p>
        <ul>
          <li><b>View History:</b> Click on <b>History</b> → <b>View History</b> to see your browsing history.</li>
          <li><b>Clear History:</b> Click on <b>History</b> → <b>Clear History</b> to delete your browsing history.</li>
          <li><b>Navigate to a History Item:</b> Double-click on any item in the history dialog to visit that page.</li>
        </ul>
        """
        layout.addWidget(QLabel(history_text))
        
        # Statistics
        layout.addWidget(QLabel("<h3>Page Statistics</h3>"))
        stats_text = """
        <p>View detailed information about the current webpage:</p>
        <ul>
          <li>Click on <b>Statistics</b> → <b>View Statistics</b> to see information about the current page.</li>
          <li>Statistics include page size, number of links, images, scripts, and more.</li>
        </ul>
        """
        layout.addWidget(QLabel(stats_text))
        
        # Keyboard Shortcuts
        layout.addWidget(QLabel("<h3>Keyboard Shortcuts</h3>"))
        shortcuts_text = """
        <table border="0" cellspacing="10">
          <tr><td><b>Enter</b></td><td>Navigate to URL in address bar</td></tr>
          <tr><td><b>Alt+Left</b></td><td>Go back</td></tr>
          <tr><td><b>Alt+Right</b></td><td>Go forward</td></tr>
          <tr><td><b>Ctrl+S</b></td><td>Save page</td></tr>
          <tr><td><b>Ctrl+D</b></td><td>Add bookmark</td></tr>
          <tr><td><b>Ctrl+B</b></td><td>View bookmarks</td></tr>
          <tr><td><b>Ctrl+H</b></td><td>View history</td></tr>
        </table>
        <p>Note: Some shortcuts may require additional implementation in future versions.</p>
        """
        layout.addWidget(QLabel(shortcuts_text))
        
        # Add Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        return dialog
    
    def create_about_dialog(self):
        """Create a dialog displaying information about the Spidy browser"""
        dialog = QDialog(self)
        dialog.setWindowTitle("About Spidy")
        dialog.resize(600, 450)
        
        # Create layout for about content
        layout = QVBoxLayout()
        
        # Helper function to create labels with word wrap and fixed width
        def create_wrapped_label(text):
            label = QLabel(text)
            label.setWordWrap(True)
            # Set a fixed width that corresponds to approximately 50 characters
            # For most fonts, this is around 300-350 pixels
            label.setFixedWidth(350)
            return label
        
        # Add about content
        title_label = QLabel("<h2>Spidy Web Browser</h2>")
        layout.addWidget(title_label)
        
        subtitle_label = create_wrapped_label("<p><i>An open-source, Python-based web browser independent from big-tech browsers</i></p>")
        layout.addWidget(subtitle_label)
        
        # Version and release info
        version_label = create_wrapped_label("<p><b>Version:</b> 0.1.0 (Development)</p>")
        layout.addWidget(version_label)
        
        build_date_label = create_wrapped_label(f"<p><b>Build Date:</b> {QDateTime.currentDateTime().toString('yyyy-MM-dd')}</p>")
        layout.addWidget(build_date_label)
        
        # Project description
        section_heading = QLabel("<h3>About the Project</h3>")
        layout.addWidget(section_heading)
        
        about_text = """
        <p>Spidy is an ambitious project to create a standards-based, open-source web browser 
        using Python. The goal is to provide a viable alternative to proprietary browsers 
        while maintaining compatibility with modern web standards.</p>
        
        <p>Development is organized into four phases:</p>
        <ol>
          <li><b>Foundation & Core Concepts:</b> Basic architecture, rendering engine selection, and core features</li>
          <li><b>Rendering Engine Development:</b> Enhanced rendering, tab management, and file operations</li>
          <li><b>Refinement & User Experience:</b> Improved UI/UX, expanded CSS support, and accessibility features</li>
          <li><b>Maintenance & Community Engagement:</b> Ongoing development and community building</li>
        </ol>
        """
        about_label = create_wrapped_label(about_text)
        layout.addWidget(about_label)
        
        # Technology stack
        tech_heading = QLabel("<h3>Technology Stack</h3>")
        layout.addWidget(tech_heading)
        
        tech_text = """
        <ul>
          <li><b>Python 3.x:</b> Primary development language</li>
          <li><b>PyQt5:</b> GUI framework</li>
          <li><b>QtWebEngine:</b> Web page rendering (based on Chromium)</li>
        </ul>
        """
        tech_label = create_wrapped_label(tech_text)
        layout.addWidget(tech_label)
        
        # License info
        license_heading = QLabel("<h3>License</h3>")
        layout.addWidget(license_heading)
        
        license_label = create_wrapped_label("<p>This software is released under the <b>MIT License</b>.</p>")
        layout.addWidget(license_label)
        
        copyright_label = create_wrapped_label("<p>Copyright © 2025 Spidy Project Contributors</p>")
        layout.addWidget(copyright_label)
        
        # Add Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        return dialog
    
    def show_help(self):
        """Show help contents dialog"""
        dialog = self.create_help_dialog()
        dialog.exec_()
        
    def show_about(self):
        """Show about dialog with information about the browser"""
        dialog = self.create_about_dialog()
        dialog.exec_()
        
    def save_page(self):
        """Save the current webpage to a file"""
        if not self.current_view():
            return
            
        current_url = self.current_view().url()
        suggested_filename = current_url.fileName()
        
        if not suggested_filename:
            suggested_filename = "webpage.html"
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Page", 
            os.path.join(os.path.expanduser("~"), suggested_filename),
            "HTML Files (*.html *.htm);;All Files (*)"
        )
        
        if filepath:
            # Ensure the filepath has an html extension if none is provided
            if not filepath.lower().endswith(('.html', '.htm')):
                filepath += '.html'
                
            def callback(success):
                if success:
                    QMessageBox.information(self, "Save Complete", 
                                           "The page has been saved successfully.")
                else:
                    QMessageBox.warning(self, "Save Failed", 
                                       "Failed to save the page. Please try again.")
            
            # Save the page and directly pass the callback function
            self.current_view().page().save(filepath, QWebEnginePage.Html, callback)

# QApplication and QtWebEngine are already initialized at the top of the file

# Create browser instance
browser = Browser()

# Save history and bookmarks on application exit
app.aboutToQuit.connect(browser.save_history)
app.aboutToQuit.connect(browser.save_bookmarks)

sys.exit(app.exec_())
