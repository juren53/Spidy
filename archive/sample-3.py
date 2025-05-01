import sys
import os
import json
from datetime import datetime
#pip install PyQt
from PyQt5.QtCore import QUrl, Qt, QDateTime
#pip install PyQtWebEngine
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import (QApplication, QLineEdit, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QMenuBar, QMenu, QAction, QMainWindow,
                            QDialog, QTableWidget, QTableWidgetItem, QHeaderView, 
                            QVBoxLayout, QDialogButtonBox, QFileDialog, QMessageBox,
                            QLabel, QGridLayout)

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize history list and config file path
        self.history = []
        self.config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        self.history_file = os.path.join(self.config_dir, 'history.json')
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Load history from file
        self.load_history()
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Simple Web Browser')
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        # Create application menu
        self.create_menu()
        
        self.url_field = QLineEdit()
        self.back_button = QPushButton('Back')
        self.forward_button = QPushButton('Forward')
        self.go_button = QPushButton('Go')
        
        # Connect navigation buttons
        self.go_button.clicked.connect(self.navigate_to_url)
        self.back_button.clicked.connect(self.view_back)
        self.forward_button.clicked.connect(self.view_forward)
        
        # Initialize with disabled navigation buttons
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        
        self.view = QWebEngineView()
        
        # Create horizontal layout for navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.forward_button)
        nav_layout.addWidget(self.url_field)
        nav_layout.addWidget(self.go_button)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(nav_layout)
        layout.addWidget(self.view)
        
        # Set layout for central widget
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)
        
        # Connect navigation signals after view is set up
        self.setup_navigation_connections()
        
        # Set initial URL
        self.view.setUrl(QUrl('http://www.google.com'))
        
        self.show()
    
    def navigate_to_url(self):
        url = self.url_field.text()
        if not url.startswith('http'):
            url = 'http://' + url
        self.view.setUrl(QUrl(url))
    
    def view_back(self):
        self.view.back()
        
    def view_forward(self):
        self.view.forward()
        
    def setup_navigation_connections(self):
        # Connect navigation signals to enable/disable buttons
        self.view.loadFinished.connect(self.update_navigation_buttons)
        self.view.urlChanged.connect(lambda: self.update_navigation_buttons())
        
        # Connect signals for history tracking
        self.view.loadFinished.connect(self.add_to_history)
        self.view.titleChanged.connect(self.update_history_title)
        
    def update_navigation_buttons(self):
        self.back_button.setEnabled(self.view.page().history().canGoBack())
        self.forward_button.setEnabled(self.view.page().history().canGoForward())
    
    def create_menu(self):
        # Use QMainWindow's built-in menuBar method
        menu_bar = self.menuBar()
        
        # Create menus
        file_menu = menu_bar.addMenu("File")
        history_menu = menu_bar.addMenu("History")
        stats_menu = menu_bar.addMenu("Statistics")
        help_menu = menu_bar.addMenu("Help")
        about_menu = menu_bar.addMenu("About")
        
        # Add actions to File menu
        save_page_action = QAction("Save Page", self)
        file_menu.addAction(save_page_action)
        save_page_action.triggered.connect(self.save_page)
        
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
    
    def add_to_history(self, success):
        """Add current page to history when loaded successfully"""
        if success:
            current_url = self.view.url().toString()
            # Only add non-empty URLs
            if current_url and current_url != "about:blank":
                # Check if this URL is already the latest in history
                if (not self.history or 
                    self.history[0].get('url') != current_url):
                    # Add to beginning of list (most recent first)
                    self.history.insert(0, {
                        'url': current_url,
                        'title': self.view.title() or current_url,
                        'timestamp': datetime.now().isoformat(),
                        'visited': 1
                    })
                    # Save after each new addition
                    self.save_history()
    
    def update_history_title(self, title):
        """Update title of current page in history if it exists"""
        if self.history:
            current_url = self.view.url().toString()
            if self.history[0].get('url') == current_url:
                self.history[0]['title'] = title
                self.save_history()
    
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
    
    def navigate_to_history_item(self, item):
        """Navigate to a URL from history"""
        if item and 'url' in item:
            self.url_field.setText(item['url'])
            self.view.setUrl(QUrl(item['url']))
    
    # Menu action implementations
    def view_history(self):
        """Show the history dialog"""
        dialog = self.create_history_dialog()
        dialog.exec_()
        
    def clear_history(self):
        """Clear browser history"""
        self.history = []
        self.save_history()
        print("History cleared")
        
    def collect_page_statistics(self, callback):
        """Collect statistics about the current webpage using JavaScript"""
        # JavaScript to collect various page statistics
        js_stats = """
        (function() {
            var stats = {};
            
            // Basic information
            stats.title = document.title;
            stats.url = window.location.href;
            stats.domain = window.location.hostname;
            stats.protocol = window.location.protocol;
            stats.path = window.location.pathname;
            
            // Page size and elements
            stats.pageSize = document.documentElement.outerHTML.length;
            stats.numLinks = document.getElementsByTagName('a').length;
            stats.numImages = document.getElementsByTagName('img').length;
            stats.numScripts = document.getElementsByTagName('script').length;
            stats.numStylesheets = document.getElementsByTagName('link').length;
            stats.numForms = document.getElementsByTagName('form').length;
            stats.numInputs = document.getElementsByTagName('input').length;
            
            // Meta information
            var metas = document.getElementsByTagName('meta');
            stats.metaTags = metas.length;
            stats.description = "";
            stats.keywords = "";
            
            for (var i = 0; i < metas.length; i++) {
                if (metas[i].getAttribute('name') === 'description') {
                    stats.description = metas[i].getAttribute('content');
                }
                if (metas[i].getAttribute('name') === 'keywords') {
                    stats.keywords = metas[i].getAttribute('content');
                }
            }
            
            return stats;
        })();
        """
        
        # Run JavaScript and process the result
        self.view.page().runJavaScript(js_stats, callback)
    
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
            
        self.collect_page_statistics(on_stats_ready)
        
    def show_help(self):
        print("Help Contents clicked")
        # Placeholder for showing help
        
    def show_about(self):
        print("About clicked")
        # Placeholder for showing about info
        
    def save_page(self):
        """Save the current webpage to a file"""
        current_url = self.view.url()
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
            self.view.page().save(filepath, QWebEnginePage.Html, callback)

app = QApplication(sys.argv)
browser = Browser()

# Save history on application exit
app.aboutToQuit.connect(browser.save_history)

sys.exit(app.exec_())
