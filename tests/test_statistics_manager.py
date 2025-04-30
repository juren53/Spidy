import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import QUrl
from statistics_manager import StatisticsManager

class TestStatisticsManager(unittest.TestCase):
    def setUp(self):
        self.browser_mock = MagicMock()
        self.stats_manager = StatisticsManager(self.browser_mock)

    def test_collect_page_statistics(self):
        """Test statistics collection when no page is loaded"""
        mock_callback = MagicMock()
        mock_view = None
        self.browser_mock.tab_manager.current_view.return_value = mock_view
        
        self.stats_manager.collect_page_statistics(mock_callback)
        
        # Verify callback was called with empty stats
        mock_callback.assert_called_once()
        args = mock_callback.call_args[0][0]
        self.assertEqual(args['title'], 'No page loaded')
        self.assertEqual(args['pageSize'], 0)

    def test_collect_page_statistics_with_page(self):
        """Test statistics collection with a loaded page"""
        mock_callback = MagicMock()
        mock_view = MagicMock()
        mock_page = MagicMock()
        
        # Mock the page's runJavaScript method
        def fake_run_js(js_code, callback):
            # Simulate JavaScript execution result
            callback({
                'title': 'Test Page',
                'url': 'https://example.com',
                'domain': 'example.com',
                'protocol': 'https:',
                'pageSize': 1000,
                'numLinks': 5,
                'numImages': 3,
                'numScripts': 2,
                'numStylesheets': 1,
                'metaTags': 4
            })
        
        mock_page.runJavaScript = fake_run_js
        mock_view.page.return_value = mock_page
        self.browser_mock.tab_manager.current_view.return_value = mock_view
        
        self.stats_manager.collect_page_statistics(mock_callback)
        
        # Verify callback was called with correct stats
        mock_callback.assert_called_once()
        args = mock_callback.call_args[0][0]
        self.assertEqual(args['title'], 'Test Page')
        self.assertEqual(args['pageSize'], 1000)
        self.assertEqual(args['numLinks'], 5)

