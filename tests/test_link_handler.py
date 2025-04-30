import unittest
from unittest.mock import MagicMock, patch, create_autospec
from datetime import datetime
from PyQt5.QtCore import QUrl, QObject
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from link_handler import LinkHandler

class TestLinkHandler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create a real QObject for the parent
        self.parent = QObject()
        
        # Create profile mock
        self.profile_mock = create_autospec(QWebEngineProfile, instance=True)
        self.profile_patcher = patch('link_handler.QWebEngineProfile.defaultProfile',
                               return_value=self.profile_mock)
        self.profile_patcher.start()
        
        # Create settings mock
        self.settings_mock = create_autospec(QWebEngineSettings, instance=True)
        
        # Create a base QWebEnginePage mock with proper initialization
        class MockWebEnginePage(QWebEnginePage):
            def __init__(self_mock, *args, **kwargs):
                # Handle both constructor signatures
                if len(args) == 1 and isinstance(args[0], QObject):
                    QWebEnginePage.__init__(self_mock, args[0])
                elif len(args) >= 1 and isinstance(args[0], QWebEngineProfile):
                    if len(args) > 1:
                        QWebEnginePage.__init__(self_mock, args[0], args[1])
                    else:
                        QWebEnginePage.__init__(self_mock, args[0])
                else:
                    QWebEnginePage.__init__(self_mock)
                
                # Set up the mock properties
                self_mock._settings_mock = self.settings_mock
                self_mock._profile_mock = self.profile_mock
                self_mock.nav_history = []
                self_mock.nav_success_count = 0
                self_mock.nav_failure_count = 0
                self_mock.current_nav_start_time = 0
                self_mock.suspicious_navigation_attempts = 0
            
            def settings(self_mock):
                return self_mock._settings_mock
            
            def profile(self_mock):
                return self_mock._profile_mock
        
        # Patch QWebEnginePage
        self.page_patcher = patch('link_handler.QWebEnginePage', MockWebEnginePage)
        self.page_patcher.start()
        
        # Initialize LinkHandler with real QObject parent
        self.link_handler = LinkHandler(self.parent)
        
        # Store the original time for consistent testing
        self.test_time = datetime.now()
        self.time_patcher = patch('time.time', return_value=self.test_time.timestamp())
        self.time_patcher.start()

    def tearDown(self):
        """Clean up test fixtures"""
        self.profile_patcher.stop()
        self.page_patcher.stop()
        self.time_patcher.stop()
        self.parent.deleteLater()  # Clean up the QObject

    def test_suspicious_url_detection(self):
        """Test the detection of suspicious URLs"""
        # Test javascript scheme
        url = QUrl("javascript:alert('test')")
        suspicious, reasons = self.link_handler.is_suspicious_url(url)
        self.assertTrue(suspicious)
        self.assertIn("Suspicious scheme: javascript", reasons)
        
        # Test suspicious hostname (using authority instead of just host)
        url = QUrl("http://malicious.com/%00test")  # Using null byte in path
        suspicious, reasons = self.link_handler.is_suspicious_url(url)
        self.assertTrue(suspicious)
        self.assertIn("Suspicious characters in URL", reasons[0])
        
        # Test very long URL
        long_url = "https://example.com/" + "x" * 2000
        url = QUrl(long_url)
        suspicious, reasons = self.link_handler.is_suspicious_url(url)
        self.assertTrue(suspicious)
        self.assertIn("Excessively long URL", reasons[0])
        
        # Test safe URL
        url = QUrl("https://example.com")
        suspicious, reasons = self.link_handler.is_suspicious_url(url)
        self.assertFalse(suspicious)
        self.assertEqual(len(reasons), 0)

    def test_navigation_request_http(self):
        """Test handling of HTTP navigation requests"""
        # Test standard HTTP navigation
        url = QUrl("http://example.com")
        result = self.link_handler.acceptNavigationRequest(
            url, 
            QWebEnginePage.NavigationTypeLinkClicked,
            True
        )
        self.assertTrue(result)
        
        # Verify navigation was recorded
        self.assertEqual(len(self.link_handler.nav_history), 1)
        entry = self.link_handler.nav_history[0]
        self.assertEqual(entry["url"], url.toString())
        self.assertEqual(entry["type"], QWebEnginePage.NavigationTypeLinkClicked)
        self.assertTrue(entry["success"])

    def test_navigation_request_file(self):
        """Test handling of file:// navigation requests"""
        # Mock os.path functions
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isabs', return_value=True):
            
            url = QUrl.fromLocalFile("/path/to/file.html")
            result = self.link_handler.acceptNavigationRequest(
                url,
                QWebEnginePage.NavigationTypeLinkClicked,
                True
            )
            self.assertTrue(result)
            
            # Verify navigation was recorded
            entry = self.link_handler.nav_history[-1]
            self.assertEqual(entry["scheme"], "file")
            self.assertTrue(entry["success"])

    def test_navigation_request_unsupported_scheme(self):
        """Test handling of unsupported URL schemes"""
        url = QUrl("custom://example.com")
        result = self.link_handler.acceptNavigationRequest(
            url,
            QWebEnginePage.NavigationTypeLinkClicked,
            False
        )
        # Should allow with warning for unknown schemes
        self.assertTrue(result)
        
        # Verify navigation was recorded with warning
        entry = self.link_handler.nav_history[-1]
        self.assertTrue("Unknown scheme" in entry.get("error", ""))

    def test_navigation_statistics(self):
        """Test navigation statistics tracking"""
        # Perform some test navigations
        url1 = QUrl("https://example.com")
        self.link_handler.acceptNavigationRequest(
            url1,
            QWebEnginePage.NavigationTypeLinkClicked,
            True
        )
        
        url2 = QUrl("javascript:alert('test')")
        self.link_handler.acceptNavigationRequest(
            url2,
            QWebEnginePage.NavigationTypeLinkClicked,
            False
        )
        
        # Get statistics
        stats = self.link_handler.get_navigation_stats()
        
        # Verify statistics
        self.assertEqual(stats["total_navigations"], 2)
        self.assertEqual(stats["successful"], 1)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["success_rate"], 50.0)
        self.assertTrue(stats["suspicious_attempts"] >= 1)

    def test_javascript_handling(self):
        """Test JavaScript message handling"""
        # Test console message handling
        with patch('builtins.print') as mock_print:
            self.link_handler.javaScriptConsoleMessage(
                0,  # Info level
                "Test message",
                42,  # Line number
                "test.js"  # Source ID
            )
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            self.assertIn("Test message", call_args)
            self.assertIn("test.js:42", call_args)

        # Test alert handling
        security_origin = MagicMock()
        security_origin.host.return_value = "example.com"
        self.link_handler.javaScriptAlert(security_origin, "Test alert")
        # Since alert is just logged, we don't need additional verification

    def test_navigation_types(self):
        """Test handling of different navigation types"""
        url = QUrl("https://example.com")
        
        # Test form submission
        self.link_handler.acceptNavigationRequest(
            url,
            QWebEnginePage.NavigationTypeFormSubmitted,
            True
        )
        self.assertEqual(
            self.link_handler.nav_history[-1]["type_name"],
            "Form Submission"
        )
        
        # Test back/forward navigation
        self.link_handler.acceptNavigationRequest(
            url,
            QWebEnginePage.NavigationTypeBackForward,
            True
        )
        self.assertEqual(
            self.link_handler.nav_history[-1]["type_name"],
            "Back/Forward Navigation"
        )
        
        # Test reload
        self.link_handler.acceptNavigationRequest(
            url,
            QWebEnginePage.NavigationTypeReload,
            True
        )
        self.assertEqual(
            self.link_handler.nav_history[-1]["type_name"],
            "Page Reload"
        )

if __name__ == '__main__':
    unittest.main()

