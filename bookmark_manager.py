"""
Bookmark Manager for Spidy Web Browser

Handles bookmark operations and persistence.
"""

import os
import json
from datetime import datetime
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QMessageBox, QPushButton
)

class BookmarkManager:
    def __init__(self, browser):
        self.browser = browser
        self.bookmarks = []
        self.bookmarks_file = os.path.join(browser.config_dir, 'bookmarks.json')
        self.load_bookmarks()

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
        current_view = self.browser.tab_manager.current_view()
        if not current_view:
            return

        current_url = current_view.url().toString()
        title = current_view.title() or current_url

        # Only add non-empty URLs
        if current_url and current_url != "about:blank":
            # Check if this URL is already bookmarked
            for bookmark in self.bookmarks:
                if bookmark.get('url') == current_url:
                    QMessageBox.information(self.browser, "Bookmark Exists",
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
            QMessageBox.information(self.browser, "Bookmark Added",
                                 f"'{title}' has been added to your bookmarks.")

    def create_bookmarks_dialog(self):
        """Create and return a dialog displaying the bookmarks"""
        dialog = QDialog(self.browser)
        dialog.setWindowTitle("Bookmarks")
        dialog.resize(780, 480)

        # Create table for bookmark items
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Title", "URL"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Fill table with bookmark items
        self._populate_bookmark_table(table)

        # Double-click on a bookmark item loads that URL and closes the dialog
        table.cellDoubleClicked.connect(lambda row, column:
                                      self.navigate_to_bookmark(self.bookmarks[row], dialog))

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(table)

        # Create button layout
        button_layout = QHBoxLayout()
        
        # Add a Remove button
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(lambda: self.remove_bookmark(table))
        button_layout.addWidget(remove_button)
        
        # Add Set as Home Page button in middle
        set_home_button = QPushButton("Set as Home Page")
        set_home_button.clicked.connect(lambda: self.set_as_home_page(table))
        button_layout.addWidget(set_home_button)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        return dialog


    def _populate_bookmark_table(self, table):
        """Populate the bookmark table with entries"""
        table.setRowCount(len(self.bookmarks))
        for i, bookmark in enumerate(self.bookmarks):
            table.setItem(i, 0, QTableWidgetItem(bookmark.get('title', '')))
            table.setItem(i, 1, QTableWidgetItem(bookmark.get('url', '')))

    def navigate_to_bookmark(self, bookmark, dialog=None):
        """Navigate to a URL from bookmarks and close the dialog if provided"""
        current_view = self.browser.tab_manager.current_view()
        if bookmark and 'url' in bookmark and current_view:
            self.browser.url_field.setText(bookmark['url'])
            current_view.setUrl(QUrl(bookmark['url']))
            # Close the bookmark dialog if it was provided
            if dialog:
                dialog.accept()

    def remove_bookmark(self, table):
        """Remove selected bookmark from the list"""
        selected_rows = sorted(set(index.row() for index in table.selectedIndexes()), reverse=True)

        if not selected_rows:
            QMessageBox.information(self.browser, "No Selection",
                                 "Please select a bookmark to remove.")
            return

        msg = ("Are you sure you want to remove this bookmark?"
               if len(selected_rows) == 1
               else f"Are you sure you want to remove {len(selected_rows)} bookmarks?")
        reply = QMessageBox.question(self.browser, "Confirm Deletion", msg,
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                if 0 <= row < len(self.bookmarks):
                    title = self.bookmarks[row].get('title', 'Bookmark')
                    del self.bookmarks[row]

            # Update the table
            self._populate_bookmark_table(table)
            self.save_bookmarks()

            if len(selected_rows) == 1:
                QMessageBox.information(self.browser, "Bookmark Removed",
                                     f"'{title}' has been removed from your bookmarks.")
            else:
                QMessageBox.information(self.browser, "Bookmarks Removed",
                                     f"{len(selected_rows)} bookmarks have been removed.")

    def view_bookmarks(self):
        """Show the bookmarks dialog"""
        dialog = self.create_bookmarks_dialog()
        dialog.exec()

    def clear_bookmarks(self):
        """Clear all bookmarks"""
        if not self.bookmarks:
            QMessageBox.information(self.browser, "No Bookmarks",
                                 "There are no bookmarks to clear.")
            return

        reply = QMessageBox.question(self.browser, "Clear Bookmarks",
                                  "Are you sure you want to clear all bookmarks?",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.bookmarks = []
            self.save_bookmarks()
            QMessageBox.information(self.browser, "Bookmarks Cleared",
                                 "All bookmarks have been cleared.")


    def set_as_home_page(self, table):
        """Set the selected bookmark as the home/startup page"""
        selected_rows = sorted(set(index.row() for index in table.selectedIndexes()))
        
        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.information(self.browser, "Invalid Selection",
                                 "Please select exactly one bookmark to set as home page.")
            return
        
        row = selected_rows[0]
        if 0 <= row < len(self.bookmarks):
            bookmark = self.bookmarks[row]
            url = bookmark.get('url', '')
            title = bookmark.get('title', 'Selected bookmark')
            
            if not url:
                QMessageBox.warning(self.browser, "Invalid Bookmark",
                                  "The selected bookmark doesn't have a valid URL.")
                return
            
            # Update the configuration if ConfigManager is available
            try:
                from config_manager import get_config
                config = get_config()
                config.set("General", "home_page", url)
                config.save_config()
                
                QMessageBox.information(self.browser, "Home Page Set",
                                      f"'{title}' has been set as your home/startup page.\n\n"
                                      f"This change will take effect the next time you start the browser.")
            except ImportError:
                # Fallback if ConfigManager is not available
                QMessageBox.warning(self.browser, "Configuration Not Available",
                                  "Cannot save home page setting. Configuration system not available.")
