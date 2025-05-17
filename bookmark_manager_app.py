#!/usr/bin/env python3
"""
Spidy Bookmark Manager

A standalone application for managing Spidy browser bookmarks.
Features:
- View bookmarks
- Edit bookmark titles and URLs
- Delete bookmarks
- Reorder bookmarks
- Save changes back to the bookmarks.json file
"""

import os
import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QHeaderView, QMessageBox, QDialog, QLabel, QLineEdit,
    QDialogButtonBox, QFileDialog, QStatusBar
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction

class EditBookmarkDialog(QDialog):
    """Dialog for editing bookmark details"""
    def __init__(self, bookmark, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Bookmark")
        self.resize(500, 120)
        
        self.bookmark = bookmark.copy()  # Work with a copy
        
        layout = QVBoxLayout()
        
        # Title input
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(bookmark.get('title', ''))
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit(bookmark.get('url', ''))
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)
    
    def get_bookmark(self):
        """Return the edited bookmark"""
        self.bookmark['title'] = self.title_edit.text()
        self.bookmark['url'] = self.url_edit.text()
        return self.bookmark

class BookmarkManagerApp(QMainWindow):
    """Main application window for bookmark management"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spidy Bookmark Manager")
        self.resize(800, 600)
        
        # Get the path to bookmarks.json
        spidy_config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        self.bookmarks_file = os.path.join(spidy_config_dir, 'bookmarks.json')
        self.bookmarks = []
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create table for bookmarks
        self.bookmark_table = QTableWidget()
        self.bookmark_table.setColumnCount(2)
        self.bookmark_table.setHorizontalHeaderLabels(["Title", "URL"])
        self.bookmark_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bookmark_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.bookmark_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.bookmark_table)
        
        # Create button row
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add New")
        self.add_button.clicked.connect(self.add_bookmark)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_bookmark)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_bookmark)
        button_layout.addWidget(self.delete_button)
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_bookmark_up)
        button_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_bookmark_down)
        button_layout.addWidget(self.move_down_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_bookmarks)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Load bookmarks
        self.load_bookmarks()
    
    def load_bookmarks(self, filename=None):
        """Load bookmarks from JSON file"""
        file_to_load = filename or self.bookmarks_file
        
        try:
            if os.path.exists(file_to_load):
                with open(file_to_load, 'r') as f:
                    self.bookmarks = json.load(f)
                self.populate_bookmark_table()
                
                self.status_bar.showMessage(f"Loaded {len(self.bookmarks)} bookmarks from {file_to_load}", 3000)
            else:
                self.status_bar.showMessage(f"Bookmark file not found: {file_to_load}", 3000)
                self.bookmarks = []
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Bookmarks", f"Failed to load bookmarks: {e}")
            self.bookmarks = []
    
    def populate_bookmark_table(self):
        """Fill the table with bookmark data"""
        self.bookmark_table.setRowCount(len(self.bookmarks))
        for i, bookmark in enumerate(self.bookmarks):
            title_item = QTableWidgetItem(bookmark.get('title', ''))
            url_item = QTableWidgetItem(bookmark.get('url', ''))
            
            self.bookmark_table.setItem(i, 0, title_item)
            self.bookmark_table.setItem(i, 1, url_item)
    
    def save_bookmarks(self):
        """Save bookmarks to the original file"""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
            self.status_bar.showMessage(f"Saved {len(self.bookmarks)} bookmarks to {self.bookmarks_file}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Bookmarks", f"Failed to save bookmarks: {e}")
            return False
    
    def get_selected_row(self):
        """Get the currently selected row"""
        selected = self.bookmark_table.selectedItems()
        if not selected:
            return -1
        return selected[0].row()
    
    def add_bookmark(self):
        """Add a new bookmark"""
        new_bookmark = {
            'title': '',
            'url': '',
            'added': datetime.now().isoformat()
        }
        
        dialog = EditBookmarkDialog(new_bookmark, self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            bookmark = dialog.get_bookmark()
            if bookmark['title'] and bookmark['url']:
                self.bookmarks.append(bookmark)
                self.populate_bookmark_table()
                self.status_bar.showMessage("Bookmark added", 3000)
            else:
                QMessageBox.warning(self, "Invalid Bookmark", "Title and URL cannot be empty")
    
    def edit_bookmark(self):
        """Edit the selected bookmark"""
        row = self.get_selected_row()
        if row < 0 or row >= len(self.bookmarks):
            QMessageBox.information(self, "No Selection", "Please select a bookmark to edit")
            return
        
        bookmark = self.bookmarks[row]
        dialog = EditBookmarkDialog(bookmark, self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            self.bookmarks[row] = dialog.get_bookmark()
            self.populate_bookmark_table()
            self.status_bar.showMessage("Bookmark updated", 3000)
    
    def delete_bookmark(self):
        """Delete the selected bookmark"""
        row = self.get_selected_row()
        if row < 0 or row >= len(self.bookmarks):
            QMessageBox.information(self, "No Selection", "Please select a bookmark to delete")
            return
        
        bookmark = self.bookmarks[row]
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete '{bookmark.get('title', 'this bookmark')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.bookmarks[row]
            self.populate_bookmark_table()
            self.status_bar.showMessage("Bookmark deleted", 3000)
    
    def move_bookmark_up(self):
        """Move the selected bookmark up in the list"""
        row = self.get_selected_row()
        if row <= 0 or row >= len(self.bookmarks):
            return
        
        # Swap with the previous bookmark
        self.bookmarks[row], self.bookmarks[row-1] = self.bookmarks[row-1], self.bookmarks[row]
        self.populate_bookmark_table()
        
        # Select the moved row
        self.bookmark_table.selectRow(row-1)
        self.status_bar.showMessage("Bookmark moved up", 3000)
    
    def move_bookmark_down(self):
        """Move the selected bookmark down in the list"""
        row = self.get_selected_row()
        if row < 0 or row >= len(self.bookmarks) - 1:
            return
        
        # Swap with the next bookmark
        self.bookmarks[row], self.bookmarks[row+1] = self.bookmarks[row+1], self.bookmarks[row]
        self.populate_bookmark_table()
        
        # Select the moved row
        self.bookmark_table.selectRow(row+1)
        self.status_bar.showMessage("Bookmark moved down", 3000)

def main():
    app = QApplication(sys.argv)
    window = BookmarkManagerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
