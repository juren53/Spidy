import unittest
from unittest.mock import MagicMock, patch
import os
import json
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMessageBox
from bookmark_manager import BookmarkManager

class TestBookmarkManager(unittest.TestCase):
    def setUp(self):
        self.browser_mock = MagicMock()
        # Mock the config directory
        self.browser_mock.config_dir = "/tmp/spidy_test"
        self.bookmark_manager = BookmarkManager(self.browser_mock)
        self.bookmark_manager.bookmarks_file = os.path.join(self.browser_mock.config_dir, 'bookmarks.json')

    def test_load_bookmarks(self):
        """Test bookmarks loading functionality"""
        test_bookmarks = [{"url": "https://example.com", "title": "Example"}]
        mock_open = unittest.mock.mock_open(read_data=json.dumps(test_bookmarks))
        with patch('builtins.open', mock_open):
            with patch('os.path.exists', return_value=True):
                self.bookmark_manager.load_bookmarks()
                self.assertEqual(len(self.bookmark_manager.bookmarks), 1)

    def test_save_bookmarks(self):
        """Test bookmarks saving functionality"""
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                self.bookmark_manager.bookmarks = [{"url": "https://example.com"}]
                self.bookmark_manager.save_bookmarks()
                mock_file.assert_called_once()

    def test_add_bookmark(self):
        """Test adding a bookmark"""
        # Mock current view
        mock_view = MagicMock()
        mock_view.url.return_value = QUrl("https://example.com")
        mock_view.title.return_value = "Example"
        
        self.browser_mock.tab_manager.current_view.return_value = mock_view
        
        # Mock file operations
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('PyQt5.QtWidgets.QMessageBox.information') as mock_info:
                    self.bookmark_manager.add_bookmark()
                    self.assertEqual(len(self.bookmark_manager.bookmarks), 1)
                    self.assertEqual(self.bookmark_manager.bookmarks[0]["url"], "https://example.com")
                    mock_info.assert_called_once()

    def test_remove_bookmark(self):
        """Test removing a bookmark"""
        # Add a test bookmark
        self.bookmark_manager.bookmarks = [
            {"url": "https://example.com", "title": "Example"}
        ]
        
        # Create mock table
        mock_table = MagicMock()
        # Create mock index with row method
        mock_index = MagicMock()
        mock_index.row = lambda: 0
        mock_table.selectedIndexes.return_value = [mock_index]
        
        # Mock file operations and dialog
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('PyQt5.QtWidgets.QMessageBox.question') as mock_question:
                    with patch('PyQt5.QtWidgets.QMessageBox.information'):
                        mock_question.return_value = QMessageBox.Yes
                        self.bookmark_manager.remove_bookmark(mock_table)
                        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)

    def test_clear_bookmarks(self):
        """Test clearing all bookmarks"""
        # Add test bookmarks
        self.bookmark_manager.bookmarks = [
            {"url": "https://example.com", "title": "Example"},
            {"url": "https://test.com", "title": "Test"}
        ]
        
        # Mock file operations and dialog
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('PyQt5.QtWidgets.QMessageBox.question') as mock_question:
                    with patch('PyQt5.QtWidgets.QMessageBox.information'):
                        mock_question.return_value = QMessageBox.Yes
                        self.bookmark_manager.clear_bookmarks()
                        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)
