"""
Unit tests for TabManager module.

Tests the functionality of tab creation, navigation, and management
in the Spidy browser.
"""

import unittest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtWidgets import QTabWidget, QPushButton, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
import sys
import os

# Create a single QApplication instance for all tests at module level
# This prevents creating multiple QApplication instances which can cause crashes
if not QApplication.instance():
    app = QApplication(sys.argv)

# Import after QApplication is created
from tab_manager import TabManager

class TestTabManager(unittest.TestCase):
    def setUp(self):
        """
        Set up test fixtures before each test.
        
        Creates mocks for browser, WebEngineView, and tab widget components
        to isolate TabManager testing from actual Qt components.
        """            
        # Create mock browser with navigation manager
        self.browser_mock = MagicMock()
        self.browser_mock.navigation_manager = MagicMock()
        
        # Create a simpler web view mock
        self.web_view_mock = MagicMock()
        self.web_view_mock.setUrl = MagicMock()
        self.web_view_mock.load = MagicMock()  # Add load method
        self.web_view_mock.url = MagicMock(return_value=QUrl())
        self.web_view_mock.deleteLater = MagicMock()
        
        # Add zoom-related methods to match WebEngineView interface
        self.web_view_mock.zoom_in = MagicMock(return_value=1.1)
        self.web_view_mock.zoom_out = MagicMock(return_value=0.9)
        self.web_view_mock.reset_zoom = MagicMock(return_value=1.0)
        self.web_view_mock.get_zoom_factor = MagicMock(return_value=1.0)
        self.web_view_mock.set_zoom_factor = MagicMock()
        
        # Create settings mock
        settings_mock = MagicMock()
        self.web_view_mock.settings = MagicMock(return_value=settings_mock)
        
        # Create page mock with title handling
        page_mock = MagicMock()
        page_mock.title = MagicMock(return_value="New Tab")
        self.web_view_mock.page = MagicMock(return_value=page_mock)
        self.web_view_mock.setPage = MagicMock()
        
        # Add simple signals that just store their last connected function
        self.web_view_mock.urlChanged = MagicMock()
        self.web_view_mock.urlChanged.connect = MagicMock()
        
        self.web_view_mock.loadFinished = MagicMock()
        self.web_view_mock.loadFinished.connect = MagicMock()
        
        self.web_view_mock.titleChanged = MagicMock()
        self.web_view_mock.titleChanged.connect = MagicMock()
        
        # Keep track of created web views
        self.created_web_views = [self.web_view_mock]
        
        # Patch WebEngineView creation - return our mock directly
        self.web_view_patcher = patch('web_view.WebEngineView', return_value=self.web_view_mock)
        self.web_view = self.web_view_patcher.start()
        
        # Patch LinkHandler to avoid Qt initialization issues
        self.link_handler_mock = MagicMock()
        self.link_handler_mock.title = MagicMock(return_value="Test Page")
        self.link_handler_patcher = patch('link_handler.LinkHandler', return_value=self.link_handler_mock)
        self.link_handler_patcher.start()
        
        # Create mock TabWidget
        self.tab_widget_mock = MagicMock(spec=QTabWidget)
        self.tab_widget_mock.currentIndex.return_value = 0
        self.tab_widget_mock.count.return_value = 0
        
        # Initialize TabManager
        self.tab_manager = TabManager(self.browser_mock)
        self.tab_manager.tab_widget = self.tab_widget_mock
        
        # Store a reference to created tabs for verification
        self.tab_manager.tabs = []

    def tearDown(self):
        """
        Clean up after each test.
        
        Stops all patches and clears references to avoid memory leaks
        and ensure a clean slate for the next test.
        """
        # Stop all patches
        self.web_view_patcher.stop()
        self.link_handler_patcher.stop()
        
        # Clear references to avoid memory leaks
        self.web_view_mock = None
        self.link_handler_mock = None
        self.tab_widget_mock = None
        self.browser_mock = None
        self.created_web_views = []

    def test_add_new_tab(self):
        """
        Test adding a new tab without specifying a URL.
        
        Verifies that:
        1. The tab is created successfully
        2. The default URL (Brave search) is loaded
        3. The navigation manager is updated with the URL
        4. The tab widget is updated appropriately
        """
        # Reset tab manager state
        self.tab_manager.tabs = []
        
        # Add a new tab
        tab = self.tab_manager.add_new_tab()
        
        # Verify tab was created
        self.assertIsNotNone(tab)
        self.assertEqual(len(self.tab_manager.tabs), 1)
        
        # Verify default URL was set
        expected_url = QUrl('https://search.brave.com/')
        self.web_view_mock.setUrl.assert_called_with(expected_url)
        
        # Verify navigation manager was updated
        self.browser_mock.navigation_manager.update_url_field.assert_called_with(expected_url)
        
        # Verify tab widget was updated
        self.tab_widget_mock.addTab.assert_called_once()
        self.tab_widget_mock.setCurrentIndex.assert_called_once()
    def test_close_tab(self):
        """
        Test closing a tab.
        
        Verifies that:
        1. The tab is removed from the tab widget
        2. The tab's resources are properly cleaned up
        3. The tab manager's internal tabs list is updated
        """
        # Reset tab manager state
        self.tab_manager.tabs = []
        
        # Set up initial state with two tabs
        self.tab_widget_mock.count.return_value = 2
        
        # Create first tab
        first_tab = self.web_view_mock
        self.tab_manager.tabs.append(first_tab)
        
        # Create second tab - use a different mock to distinguish them
        second_tab = MagicMock()
        second_tab.deleteLater = MagicMock()
        self.tab_manager.tabs.append(second_tab)
        
        # Reset mocks before the test
        self.tab_widget_mock.removeTab.reset_mock()
        first_tab.deleteLater.reset_mock()
        
        # Close first tab
        self.tab_manager.close_tab(0)
        
        # Verify cleanup
        self.tab_widget_mock.removeTab.assert_called_once_with(0)
        first_tab.deleteLater.assert_called_once()
        self.assertEqual(len(self.tab_manager.tabs), 1)
        self.assertEqual(self.tab_manager.tabs[0], second_tab)

    def test_next_tab(self):
        """
        Test switching to the next tab.
        
        Verifies that:
        1. The tab widget's current index is updated correctly
        2. When at the last tab, it wraps around to the first tab
        """
        # Reset mock call history
        self.tab_widget_mock.setCurrentIndex.reset_mock()
        
        # Set up initial state - current tab is middle tab (index 1)
        self.tab_widget_mock.currentIndex.return_value = 1
        self.tab_widget_mock.count.return_value = 3
        
        # Switch to next tab
        self.tab_manager.next_tab()
        
        # Verify tab switch - should go to index 2
        self.tab_widget_mock.setCurrentIndex.assert_called_once_with(2)
        
        # Reset mock and set up for wrap-around test
        self.tab_widget_mock.setCurrentIndex.reset_mock()
        self.tab_widget_mock.currentIndex.return_value = 2  # Last tab
        
        # Switch to next tab (should wrap to first)
        self.tab_manager.next_tab()
        
        # Verify wrap-around to first tab (index 0)
        self.tab_widget_mock.setCurrentIndex.assert_called_once_with(0)
    def test_previous_tab(self):
        """
        Test switching to the previous tab.
        
        Verifies that:
        1. The tab widget's current index is updated correctly
        2. When at the first tab, it wraps around to the last tab
        """
        # Reset mock call history
        self.tab_widget_mock.setCurrentIndex.reset_mock()
        
        # Set up initial state - current tab is middle tab (index 1)
        self.tab_widget_mock.currentIndex.return_value = 1
        self.tab_widget_mock.count.return_value = 3
        
        # Switch to previous tab
        self.tab_manager.previous_tab()
        
        # Verify tab switch - should go to index 0
        self.tab_widget_mock.setCurrentIndex.assert_called_once_with(0)
        
        # Reset mock and set up for wrap-around test
        self.tab_widget_mock.setCurrentIndex.reset_mock()
        self.tab_widget_mock.currentIndex.return_value = 0  # First tab
        
        # Switch to previous tab (should wrap to last)
        self.tab_manager.previous_tab()
        
        # Verify wrap-around to last tab (index 2)
        self.tab_widget_mock.setCurrentIndex.assert_called_once_with(2)
        
    def test_add_new_tab_with_url(self):
        """
        Test adding a new tab with specific URL.
        
        Verifies that:
        1. The correct URL is loaded in the web view
        2. The navigation manager's URL field is updated
        3. The tab title is updated appropriately
        """
        # Reset tabs and mocks
        self.tab_manager.tabs = []
        self.web_view_mock.setUrl.reset_mock()
        self.browser_mock.navigation_manager.update_url_field.reset_mock()
        
        # Add tab with custom URL
        url = QUrl('https://example.com')
        tab = self.tab_manager.add_new_tab(url)
        
        # Verify URL was set
        self.web_view_mock.setUrl.assert_called_with(url)
        
        # Verify navigation manager was updated
        self.browser_mock.navigation_manager.update_url_field.assert_called_with(url)
        
        # Test tab title update
        self.tab_widget_mock.setTabText.reset_mock()
        self.tab_manager.update_tab_title(self.web_view_mock)
