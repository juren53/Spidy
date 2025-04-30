import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication
import sys
from browser import Browser

# Required for QWebEngine components
_app = None

class TestBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize QApplication instance"""
        global _app
        _app = QApplication.instance()
        if _app is None:
            _app = QApplication(sys.argv)
        
        # Mock QtWebEngine initialization
        with patch('PyQt5.QtWebEngine.QtWebEngine.initialize'):
            cls.qtwebengine_patch = patch('PyQt5.QtWebEngineWidgets.QWebEngineView')
            cls.qtwebengine_mock = cls.qtwebengine_patch.start()

    def setUp(self):
        """Set up test browser instance"""
        # Mock necessary components
        with patch('PyQt5.QtWebEngineWidgets.QWebEngineSettings'):
            with patch('os.makedirs'):
                with patch('PyQt5.QtWebEngine.QtWebEngine.initialize'):
                    self.browser = Browser()
                    
                    # Mock managers
                    self.browser.tab_manager = MagicMock()
                    self.browser.navigation_manager = MagicMock()
                    self.browser.bookmark_manager = MagicMock()
                    self.browser.statistics_manager = MagicMock()

    @classmethod
    def tearDownClass(cls):
        """Clean up patches"""
        cls.qtwebengine_patch.stop()

    def test_keyboard_navigation(self):
        """Test keyboard navigation handling"""
        # Mock key press event
        event = MagicMock()
        event.key = MagicMock(return_value=Qt.Key_Left)
        
        # Mock current view
        mock_view = MagicMock()
        mock_page = MagicMock()
        mock_history = MagicMock()
        mock_history.canGoBack.return_value = True
        mock_page.history.return_value = mock_history
        mock_view.page.return_value = mock_page
        
        self.browser.tab_manager.current_view.return_value = mock_view
        
        self.browser.keyPressEvent(event)
        self.browser.navigation_manager.view_back.assert_called_once()

    def test_save_page(self):
        """Test page saving functionality"""
        mock_view = MagicMock()
        mock_page = MagicMock()
        mock_view.page.return_value = mock_page
        mock_view.url.return_value = QUrl("https://example.com")
        
        self.browser.tab_manager.current_view.return_value = mock_view
        
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            with patch('PyQt5.QtWidgets.QMessageBox.information'):
                mock_dialog.return_value = ("/tmp/test.html", "")
                self.browser.save_page()
                mock_page.save.assert_called_once_with("/tmp/test.html")

    def test_open_file(self):
        """Test file opening functionality"""
        with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = ("/tmp/test.html", "")
            self.browser.open_file()
            self.browser.tab_manager.add_new_tab.assert_called_once()
