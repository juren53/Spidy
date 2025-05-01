"""
Spidy Web Browser - Main Browser Class

A standards-based, open-source web browser built with Python and PyQt5.
Provides basic browsing functionality, bookmarks, history tracking, and statistics.
"""

import os
import subprocess
import sys
from datetime import datetime
from PyQt5.QtCore import Qt, QUrl, QDateTime
from PyQt5.QtWidgets import QMainWindow, QWidget, QFileDialog, QMessageBox, QApplication
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QToolBar, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile, QWebEngineScript
from navigation_manager import NavigationManager
from tab_manager import TabManager
from bookmark_manager import BookmarkManager
from ui_manager import UIManager
from statistics_manager import StatisticsManager

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize configuration directory
        self.config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize manager classes
        self.tab_manager = TabManager(self)
        self.navigation_manager = NavigationManager(self)
        self.bookmark_manager = BookmarkManager(self)
        self.statistics_manager = StatisticsManager(self)
        self.ui_manager = UIManager(self)
        self._configure_global_settings()

        # Create initial tab
        self.tab_manager.add_new_tab(QUrl('https://search.brave.com/'))
        
        self.show()

    def _configure_global_settings(self):
        """Configure global browser settings"""
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        # Enable JavaScript
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        # Some Qt versions have a specific setting for WebAssembly
        try:
            if hasattr(QWebEngineSettings, "WebAssemblyEnabled"):
                settings.setAttribute(QWebEngineSettings.WebAssemblyEnabled, True)
        except Exception as e:
            print(f"WebAssembly setting not supported: {e}")
        
        # Configure WebAssembly settings
        profile = QWebEngineProfile.defaultProfile()
        
        # Create a script collection to set a properly formatted CSP
        csp_script_content = """
        (function() {
            try {
                // Use a properly formatted WebAssembly CSP directive
                const meta = document.createElement('meta');
                meta.httpEquiv = 'Content-Security-Policy';
                meta.content = "script-src 'self' 'unsafe-eval' blob: https:; object-src 'self';";
                
                // Insert it at the beginning of the head if possible
                if (document.head) {
                    document.head.insertBefore(meta, document.head.firstChild);
                }
                console.log('[Spidy Browser] CSP with WebAssembly support configured');
            } catch (e) {
                console.error('[Spidy Browser] CSP setup error:', e);
            }
        })();
        """
        
        # Create a QWebEngineScript object
        csp_script = QWebEngineScript()
        csp_script.setName("setCSP")
        csp_script.setSourceCode(csp_script_content)
        csp_script.setInjectionPoint(QWebEngineScript.DocumentReady)
        csp_script.setRunsOnSubFrames(True)
        csp_script.setWorldId(QWebEngineScript.MainWorld)
        
        # Add the script to the collection
        profile.scripts().insert(csp_script)

    def keyPressEvent(self, event):
        """Handle keyboard navigation events"""
        current_view = self.tab_manager.current_view()
        if not current_view:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_Left and current_view.page().history().canGoBack():
            self.navigation_manager.view_back()
        elif event.key() == Qt.Key_Right and current_view.page().history().canGoForward():
            self.navigation_manager.view_forward()
        else:
            super().keyPressEvent(event)

    def open_file(self):
        """Open a local HTML or MD file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            os.path.expanduser("~"),
            "Web Files (*.html *.htm *.md);;HTML Files (*.html *.htm);;Markdown Files (*.md);;All Files (*)"
        )
        
        if filepath:
            url = QUrl.fromLocalFile(os.path.abspath(filepath))
            self.tab_manager.add_new_tab(url)

    def save_page(self):
        """Save the current webpage to a file"""
        current_view = self.tab_manager.current_view()
        if not current_view:
            return
            
        current_url = current_view.url()
        suggested_filename = current_url.fileName() or "webpage.html"
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Page", 
            os.path.join(os.path.expanduser("~"), suggested_filename),
            "HTML Files (*.html *.htm);;All Files (*)"
        )
        
        if filepath:
            if not filepath.lower().endswith(('.html', '.htm')):
                filepath += '.html'
                
            # Simply call save with the filepath
            current_view.page().save(filepath)
            QMessageBox.information(self, "Save Complete", 
                                  "The page has been saved successfully.")

    def closeEvent(self, event):
        """Handle application close event"""
        self.navigation_manager.save_history()
        self.bookmark_manager.save_bookmarks()
        super().closeEvent(event)

    def view_statistics(self):
        """Show statistics about the current webpage"""
        self.statistics_manager.view_statistics()

    def show_help(self):
        """Show help dialog"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Spidy Help")
        help_dialog.resize(500, 400)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>Spidy Browser Help</h2>"))
        layout.addWidget(QLabel("""
            <p>Welcome to Spidy, an open-source web browser built with Python and PyQt5!</p>
            <h3>Basic Navigation</h3>
            <ul>
                <li>Use the URL bar to enter websites</li>
                <li>Use Back/Forward buttons to navigate history</li>
                <li>Use Ctrl+T to open new tabs</li>
                <li>Use Ctrl+W to close current tab</li>
            </ul>
            <h3>Features</h3>
            <ul>
                <li>Bookmark your favorite pages</li>
                <li>View browsing history</li>
                <li>View page statistics</li>
                <li>Save pages locally</li>
            </ul>
        """))

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(help_dialog.reject)
        layout.addWidget(button_box)

        help_dialog.setLayout(layout)
        help_dialog.exec_()

    def show_about(self):
        """Show about dialog"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Spidy")
        about_dialog.resize(400, 300)

        # Get the last git commit date dynamically
        try:
            last_commit = subprocess.check_output(
                ['git', 'log', '-1', '--format=%cd', '--date=iso'],
                text=True, stderr=subprocess.PIPE
            ).strip()
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error retrieving git commit date: {e}")
            last_commit = "Not available"

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>Spidy Web Browser</h2>"))
        layout.addWidget(QLabel(f"""
            <p>Version 1.0</p>
            <p>An open-source web browser built with Python and PyQt5.</p>
            <p>Features:</p>
            <ul>
                <li>Multiple tabs</li>
                <li>Bookmarks</li>
                <li>History tracking</li>
                <li>Page statistics</li>
                <li>Security-focused navigation</li>
            </ul>
            <p>Last Commit: {last_commit}</p>
            <p>Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %z')}</p>
            <p>&copy; 2025 Spidy Project</p>
        """))

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(about_dialog.reject)
        layout.addWidget(button_box)

        about_dialog.setLayout(layout)
        about_dialog.exec_()

