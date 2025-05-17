#!/usr/bin/env python3
"""
Test script for WebEngineView context menu functionality in Spidy browser.

This script tests whether the contextMenuEvent method in WebEngineView properly
preserves the "Open Link in New Tab" action when right-clicking on hyperlinks.
"""

import sys
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt, QPoint, QUrl
from PyQt6.QtGui import QAction, QContextMenuEvent
from PyQt6.QtWidgets import QApplication, QMenu

# Import the WebEngineView class from web_view.py
from web_view import WebEngineView

class TestContextMenu:
    """Test class for WebEngineView context menu functionality."""
    
    def __init__(self):
        """Initialize test variables."""
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # Test results
        self.test_results = {
            "link_context_menu_has_open_in_new_tab": False,
            "regular_context_menu_actions_preserved": False,
            "view_source_action_customized": False
        }
    
    def setup_mocks(self):
        """Set up mock objects for testing."""
        # Create a mock context menu event
        self.context_event = MagicMock(spec=QContextMenuEvent)
        self.context_event.globalPos.return_value = QPoint(100, 100)
        
        # Mock a standard context menu with link actions
        self.link_menu = QMenu()
        
        # Add typical actions found in a link context menu
        self.open_link_action = QAction("Open Link in New Tab", self.link_menu)
        self.copy_link_action = QAction("Copy Link Address", self.link_menu)
        self.open_link_window_action = QAction("Open Link in New Window", self.link_menu)
        self.view_source_action = QAction("View Page Source", self.link_menu)
        
        self.link_menu.addAction(self.open_link_action)
        self.link_menu.addAction(self.copy_link_action)
        self.link_menu.addAction(self.open_link_window_action)
        self.link_menu.addSeparator()
        self.link_menu.addAction(self.view_source_action)
    
    def create_test_web_view(self):
        """Create a test WebEngineView instance with mocked methods."""
        # Create the WebEngineView instance
        self.web_view = WebEngineView()
        
        # Mock the createStandardContextMenu method to return our mock menu
        self.web_view.createStandardContextMenu = MagicMock(return_value=self.link_menu)
        
        # Mock the exec method of QMenu to prevent GUI display
        self.link_menu.exec = MagicMock()
        
        # Mock the view_page_source method to avoid actual execution
        self.web_view.view_page_source = MagicMock()
    
    def run_link_menu_test(self):
        """Test whether Open Link in New Tab action is preserved."""
        print("Running test: Context menu on hyperlink")
        
        # Call the contextMenuEvent method with our mock event
        self.web_view.contextMenuEvent(self.context_event)
        
        # Check if Open Link in New Tab action is still in the menu
        actions_after = [action.text() for action in self.link_menu.actions()]
        self.test_results["link_context_menu_has_open_in_new_tab"] = "Open Link in New Tab" in actions_after
        
        # Check if other regular actions are preserved
        self.test_results["regular_context_menu_actions_preserved"] = (
            "Copy Link Address" in actions_after and
            "Open Link in New Window" in actions_after
        )
        
        # Check if View Page Source action is connected to our custom method
        view_source_connected = False
        for action in self.link_menu.actions():
            if action.text() == "View Page Source":
                # Since we mocked view_page_source, we can check if it was called
                # when the action is triggered
                action.trigger()
                view_source_connected = self.web_view.view_page_source.called
                break
        
        self.test_results["view_source_action_customized"] = view_source_connected
    
    def print_results(self):
        """Print test results."""
        print("\n===== TEST RESULTS =====")
        all_passed = True
        
        for test_name, result in self.test_results.items():
            status = "PASS" if result else "FAIL"
            if not result:
                all_passed = False
            print(f"{test_name}: {status}")
        
        print("\nSUMMARY:")
        if all_passed:
            print("✅ All tests PASSED. The WebEngineView.contextMenuEvent method correctly preserves the 'Open Link in New Tab' functionality.")
        else:
            print("❌ Some tests FAILED. There may still be issues with the context menu implementation.")
        
        if self.test_results["link_context_menu_has_open_in_new_tab"]:
            print("\n'Open Link in New Tab' action is correctly preserved in the context menu.")
        else:
            print("\n'Open Link in New Tab' action is missing from the context menu.")
    
    def run_all_tests(self):
        """Run all tests."""
        self.setup_mocks()
        self.create_test_web_view()
        self.run_link_menu_test()
        self.print_results()

if __name__ == "__main__":
    test = TestContextMenu()
    test.run_all_tests()

