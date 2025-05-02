"""
Navigation Manager for Spidy Web Browser

Handles URL navigation, history tracking, and navigation-related UI updates.
"""

import os
import json
from datetime import datetime
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QHeaderView, QDialogButtonBox, QMessageBox

class NavigationManager:
    def __init__(self, browser):
        self.browser = browser
        self.history = []
        self.history_file = os.path.join(browser.config_dir, 'history.json')
        self.load_history()
        
    def navigate_to_url(self):
        """Navigate to URL in current tab"""
        url = self.browser.url_field.text()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        current_view = self.browser.tab_manager.current_view()
        if current_view:
            current_view.setUrl(QUrl(url))

    def view_back(self):
        """Navigate back in current tab"""
        current_view = self.browser.tab_manager.current_view()
        if current_view:
            current_view.back()

    def view_forward(self):
        """Navigate forward in current tab"""
        current_view = self.browser.tab_manager.current_view()
        if current_view:
            current_view.forward()

    def reload_page(self):
        """Reload current tab"""
        current_view = self.browser.tab_manager.current_view()
        if current_view:
            current_view.reload()

    def update_url_field(self, url, browser=None):
        """Update URL field when tab URL changes"""
        current_view = self.browser.tab_manager.current_view()
        if not browser or browser == current_view:
            self.browser.url_field.setText(url.toString())

    def update_navigation_buttons(self):
        """Update navigation button states for current tab"""
        current_view = self.browser.tab_manager.current_view()
        if current_view:
            self.browser.back_button.setEnabled(current_view.page().history().canGoBack())
            self.browser.forward_button.setEnabled(current_view.page().history().canGoForward())

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
    
    def add_to_history(self, success, browser=None):
        """Add current page to history when loaded successfully"""
        current_view = self.browser.tab_manager.current_view()
        if success and (not browser or browser == current_view):
            current_url = current_view.url().toString()
            if current_url and current_url != "about:blank":
                if not self.history or self.history[0].get('url') != current_url:
                    self.history.insert(0, {
                        'url': current_url,
                        'title': current_view.title() or current_url,
                        'timestamp': datetime.now().isoformat(),
                        'visited': 1
                    })
                    self.save_history()

    def update_history_title(self, title, browser=None):
        """Update the title in history for the current URL"""
        current_view = self.browser.tab_manager.current_view()
        if not browser or browser == current_view:
            current_url = current_view.url().toString()
            # Update title in history for the current URL
            for entry in self.history:
                if entry.get('url') == current_url:
                    entry['title'] = title
                    self.save_history()
                    break

    def create_history_dialog(self):
        """Create and return a dialog displaying the browser history"""
        dialog = QDialog(self.browser)
        dialog.setWindowTitle("Browsing History")
        dialog.resize(840, 520)
        
        # Create table for history items
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Title", "URL", "Date/Time"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Create a smaller font for the table
        small_font = QFont()
        small_font.setPointSize(9)  # Adjust this value as needed
        table.setFont(small_font)
        
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
        current_view = self.browser.tab_manager.current_view()
        if history_item and 'url' in history_item and current_view:
            self.browser.url_field.setText(history_item['url'])
            current_view.setUrl(QUrl(history_item['url']))
    
    def view_history(self):
        """Show the history dialog"""
        dialog = self.create_history_dialog()
        dialog.exec_()
        
    def clear_history(self):
        """Clear browser history"""
        if not self.history:
            QMessageBox.information(self.browser, "No History", 
                                  "There is no browsing history to clear.")
            return
            
        reply = QMessageBox.question(self.browser, "Clear History", 
                                   "Are you sure you want to clear all browsing history?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.history = []
            self.save_history()
            QMessageBox.information(self.browser, "History Cleared", 
                                  "All browsing history has been cleared.")
            print("History cleared")

