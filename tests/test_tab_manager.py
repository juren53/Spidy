import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtWidgets import QTabWidget, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from tab_manager import TabManager

class TestTabManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create mock browser with navigation manager
        self.browser_mock = MagicMock()
        self.browser_mock.navigation_manager = MagicMock()
        
        # Create signal tracking for created web views
        self.created_web_views = []
        
        # Create factory for QWebEngineView mocks
        def create_web_view():
            mock_view = MagicMock(spec=QWebEngineView)
            
            # Mock basic methods
            mock_view.setUrl = MagicMock()
            mock_view.url = MagicMock(return_value=QUrl())
            mock_view.deleteLater = MagicMock()
            
            # Create settings mock
            settings_mock = MagicMock(spec=QWebEngineSettings)
            mock_view.settings = MagicMock(return_value=settings_mock)
            
            # Create page mock with title handling
            page_mock = MagicMock()
            page_mock.title = MagicMock(return_value="New Tab")
            mock_view.page = MagicMock(return_value=page_mock)
            
            # Create working signals
            def create_signal():
                signal = MagicMock()
                callbacks = []
                def connect(callback):
                    callbacks.append(callback)
                    return callback
                def emit(*args):
                    for cb in callbacks:
                        if len(args) > 0:
                            cb(*args)
                        else:
                            cb()
                signal.connect = connect
                signal.emit = emit
                return signal
            
            # Set up all required signals
            mock_view.urlChanged = create_signal()
            mock_view.loadFinished = create_signal()
            mock_view.titleChanged = create_signal()
            
            # Track the instance
            self.created_web_views.append(mock_view)
            return mock_view
        
        # Patch QWebEngineView creation
        self.web_view_patcher = patch('tab_manager.QWebEngineView', 
                                    side_effect=create_web_view)
        self.web_view_patcher.start()
        
        # Patch LinkHandler to avoid Qt initialization issues
        link_handler_mock = MagicMock()
        link_handler_mock.title = MagicMock(return_value="Test Page")
        self.link_handler_patcher = patch('tab_manager.LinkHandler', 
                                        return_value=link_handler_mock)
        self.link_handler_patcher.start()
        
        # Create mock TabWidget
        self.tab_widget_mock = MagicMock(spec=QTabWidget)
        self.tab_widget_mock.currentIndex.return_value = 0
        self.tab_widget_mock.count.return_value = 0
        
        # Initialize TabManager
        self.tab_manager = TabManager(self.browser_mock)
        self.tab_manager.tab_widget = self.tab_widget_mock

    def tearDown(self):
        """Clean up patches"""
        self.web_view_patcher.stop()
        self.link_handler_patcher.stop()

    def test_add_new_tab(self):
        """Test adding a new tab"""
        # Add a new tab
        tab = self.tab_manager.add_new_tab()
        
        # Verify tab was created
        self.assertIsNotNone(tab)
        self.assertEqual(len(self.tab_manager.tabs), 1)
        
        # Verify default URL was set
        expected_url = QUrl('https://search.brave.com/')
        web_view = self.created_web_views[-1]
        web_view.setUrl.assert_called_with(expected_url)
        
        # Verify navigation manager was updated
        self.browser_mock.navigation_manager.update_url_field.assert_called_with(expected_url)
        
        # Verify tab widget was updated
        self.tab_widget_mock.addTab.assert_called_once()
        self.tab_widget_mock.setCurrentIndex.assert_called_once()
    def test_add_new_tab_with_url(self):
        """Test adding a new tab with specific URL"""
        # Add tab with custom URL
        url = QUrl('https://example.com')
        tab = self.tab_manager.add_new_tab(url)
        
        # Verify URL was set
        web_view = self.created_web_views[-1]
        web_view.setUrl.assert_called_with(url)
        
        # Verify navigation manager was updated
        self.browser_mock.navigation_manager.update_url_field.assert_called_with(url)
    def test_close_tab(self):
        """Test closing a tab"""
        # Set up initial state with two tabs
        self.tab_widget_mock.count.return_value = 2
        first_tab = self.tab_manager.add_new_tab()
        second_tab = self.tab_manager.add_new_tab()
        
        # Reset mocks after setup
        self.tab_widget_mock.removeTab.reset_mock()
        first_tab.deleteLater.reset_mock()
        
        # Close first tab
        self.tab_manager.close_tab(0)
        
        # Verify cleanup
        self.tab_widget_mock.removeTab.assert_called_once_with(0)
        first_tab.deleteLater.assert_called_once()
        self.assertEqual(len(self.tab_manager.tabs), 1)

    def test_next_tab(self):
        """Test switching to next tab"""
        # Set up initial state
        self.tab_widget_mock.currentIndex.return_value = 1
        self.tab_widget_mock.count.return_value = 3
        
        # Switch to next tab
        self.tab_manager.next_tab()
        
        # Verify tab switch
        self.tab_widget_mock.setCurrentIndex.assert_called_once_with(2)

    def test_previous_tab(self):
        """Test switching to previous tab"""
        # Set up initial state
        self.tab_widget_mock.currentIndex.return_value = 1
        self.tab_widget_mock.count.return_value = 3
        
        # Switch to previous tab
        self.tab_manager.previous_tab()
        
        # Verify tab switch
        self.tab_widget_mock.setCurrentIndex.assert_called_once_with(0)

    def test_update_tab_title(self):
        """Test updating tab title"""
        # Create a tab
        tab = self.tab_manager.add_new_tab()
        web_view = self.created_web_views[-1]
        self.tab_widget_mock.indexOf.return_value = 0
        
        # Reset setTabText mock
        self.tab_widget_mock.setTabText.reset_mock()
        
        # Case 1: Regular title
        web_view.page().title.return_value = "Test Page"
        self.tab_manager.update_tab_title(web_view)
        self.tab_widget_mock.setTabText.assert_called_with(0, "Test Page")
        
        # Case 2: Long title
        long_title = "This is a very long title that should be truncated"
        web_view.page().title.return_value = long_title
        self.tab_manager.update_tab_title(web_view)
        self.tab_widget_mock.setTabText.assert_called_with(0, long_title[:20] + "...")
        
        # Case 3: Empty title
        web_view.page().title.return_value = ""
        self.tab_manager.update_tab_title(web_view)
        self.tab_widget_mock.setTabText.assert_called_with(0, "New Tab")
