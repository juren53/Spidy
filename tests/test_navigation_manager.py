import unittest
from unittest.mock import MagicMock, patch
import json
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMessageBox
from navigation_manager import NavigationManager

class TestNavigationManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.browser_mock = MagicMock()
        # Mock the config directory
        self.browser_mock.config_dir = "/tmp/spidy_test"
        self.nav_manager = NavigationManager(self.browser_mock)
        self.nav_manager.history_file = os.path.join(self.browser_mock.config_dir, 'history.json')

    def test_load_history(self):
        """Test history loading functionality"""
        test_history = [{"url": "https://example.com", "title": "Example"}]
        mock_open = unittest.mock.mock_open(read_data=json.dumps(test_history))
        with patch('builtins.open', mock_open):
            with patch('os.path.exists', return_value=True):
                self.nav_manager.load_history()
                self.assertEqual(len(self.nav_manager.history), 1)

    def test_save_history(self):
        """Test history saving functionality"""
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                self.nav_manager.history = [{"url": "https://example.com"}]
                self.nav_manager.save_history()
                mock_file.assert_called_once()

    def test_navigate_to_url(self):
        """Test URL navigation"""
        # Mock current view
        mock_view = MagicMock()
        self.browser_mock.tab_manager.current_view.return_value = mock_view
        self.browser_mock.url_field.text.return_value = "example.com"
        
        self.nav_manager.navigate_to_url()
        mock_view.setUrl.assert_called_once()
        called_url = mock_view.setUrl.call_args[0][0]
        self.assertEqual(called_url.toString(), "http://example.com")

    def test_update_navigation_buttons(self):
        """Test navigation button state updates"""
        # Mock current view with history
        mock_view = MagicMock()
        mock_page = MagicMock()
        mock_history = MagicMock()
        
        # Set history states
        mock_history.canGoBack.return_value = True
        mock_history.canGoForward.return_value = False
        mock_page.history.return_value = mock_history
        mock_view.page.return_value = mock_page
        
        self.browser_mock.tab_manager.current_view.return_value = mock_view
        self.nav_manager.update_navigation_buttons()
        
        # Verify button states were updated correctly
        self.browser_mock.back_button.setEnabled.assert_called_with(True)
        self.browser_mock.forward_button.setEnabled.assert_called_with(False)

    def test_add_to_history(self):
        """Test adding entries to history"""
        # Mock current view
        mock_view = MagicMock()
        mock_view.url.return_value = QUrl("https://example.com")
        mock_view.title.return_value = "Example"
        
        self.browser_mock.tab_manager.current_view.return_value = mock_view
        
        # Mock file operations
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('os.path.exists', return_value=True):
                self.nav_manager.add_to_history(True)
                self.assertEqual(len(self.nav_manager.history), 1)
                self.assertEqual(self.nav_manager.history[0]["url"], "https://example.com")

    def test_clear_history(self):
        """Test history clearing"""
        # Add some test history
        self.nav_manager.history = [
            {"url": "https://example.com", "title": "Example"},
            {"url": "https://test.com", "title": "Test"}
        ]
        
        # Mock file operations and dialog
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('PyQt5.QtWidgets.QMessageBox.question') as mock_question:
                    with patch('PyQt5.QtWidgets.QMessageBox.information'):
                        # Set the return value to Yes
                        mock_question.return_value = QMessageBox.Yes
                        
                        # Call clear_history
                        self.nav_manager.clear_history()
                        
                        # Verify history was cleared
                        self.assertEqual(len(self.nav_manager.history), 0)
                        mock_question.assert_called_once()
