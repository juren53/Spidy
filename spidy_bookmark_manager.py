#!/usr/bin/env python3
"""
Spidy Bookmark Manager - A simple GUI tool for managing Spidy browser bookmarks.
"""

import os
import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
    QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QHeaderView, 
    QMessageBox, QDialog, QLabel, QLineEdit, QDialogButtonBox, QStatusBar
)

class EditBookmarkDialog(QDialog):
    """Dialog for editing bookmark details"""
    def __init__(self, bookmark, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Bookmark")
        self.resize(500, 150)
        
        self.bookmark = bookmark.copy()  # Work with a copy
        
        layout = QVBoxLayout(self)
        
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
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_bookmark(self):
        """Return the edited bookmark"""
        self.bookmark['title'] = self.title_edit.text()
        self.bookmark['url'] = self.url_edit.text()
        return self.bookmark

class BookmarkManager(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spidy Bookmark Manager")
        self.resize(800, 600)
        
        # Get path to bookmarks file
        spidy_config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        self.bookmarks_file = os.path.join(spidy_config_dir, 'bookmarks.json')
        self.bookmarks = []
        
        # Setup UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Bookmark table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Title", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Button row
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_bookmark)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_bookmark)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_bookmark)
        button_layout.addWidget(delete_btn)
        
        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self.move_up)
        button_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self.move_down)
        button_layout.addWidget(move_down_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_bookmarks)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Load bookmarks
        self.load_bookmarks()
    
    def load_bookmarks(self):
        """Load bookmarks from file"""
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
                self.update_table()
                self.status_bar.showMessage(f"Loaded {len(self.bookmarks)} bookmarks", 3000)
            else:
                self.status_bar.showMessage("Bookmark file not found", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load bookmarks: {e}")
    
    def update_table(self):
        """Update the table with current bookmarks"""
        self.table.setRowCount(len(self.bookmarks))
        for i, bookmark in enumerate(self.bookmarks):
            self.table.setItem(i, 0, QTableWidgetItem(bookmark.get('title', '')))
            self.table.setItem(i, 1, QTableWidgetItem(bookmark.get('url', '')))
    
    def get_selected_row(self):
        """Get the currently selected row index"""
        selected = self.table.selectedItems()
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
        if dialog.exec() == QDialog.DialogCode.Accepted:
            bookmark = dialog.get_bookmark()
            if bookmark['title'] and bookmark['url']:
                self.bookmarks.append(bookmark)
                self.update_table()
                self.status_bar.showMessage("Bookmark added", 3000)
            else:
                QMessageBox.warning(self, "Error", "Title and URL cannot be empty")
    
    def edit_bookmark(self):
        """Edit the selected bookmark"""
        row = self.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "Info", "Please select a bookmark to edit")
            return
        
        dialog = EditBookmarkDialog(self.bookmarks[row], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.bookmarks[row] = dialog.get_bookmark()
            self.update_table()
            self.status_bar.showMessage("Bookmark updated", 3000)
    
    def delete_bookmark(self):
        """Delete the selected bookmark"""
        row = self.get_selected_row()
        if row < 0:
            QMessageBox.information(self, "Info", "Please select a bookmark to delete")
            return
        
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to delete this bookmark?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.bookmarks[row]
            self.update_table()
            self.status_bar.showMessage("Bookmark deleted", 3000)
    
    def move_up(self):
        """Move the selected bookmark up in the list"""
        row = self.get_selected_row()
        if row <= 0:
            return
            
        self.bookmarks[row], self.bookmarks[row-1] = self.bookmarks[row-1], self.bookmarks[row]
        self.update_table()
        self.table.selectRow(row-1)
        self.status_bar.showMessage("Bookmark moved up", 3000)
    
    def move_down(self):
        """Move the selected bookmark down in the list"""
        row = self.get_selected_row()
        if row < 0 or row >= len(self.bookmarks) - 1:
            return
            
        self.bookmarks[row], self.bookmarks[row+1] = self.bookmarks[row+1], self.bookmarks[row]
        self.update_table()
        self.table.selectRow(row+1)
        self.status_bar.showMessage("Bookmark moved down", 3000)
    
    def save_bookmarks(self):
        """Save bookmarks to file"""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
            self.status_bar.showMessage("Bookmarks saved successfully", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save bookmarks: {e}")

def main():
    app = QApplication(sys.argv)
    window = BookmarkManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
