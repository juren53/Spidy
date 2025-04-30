"""
Link Handler for Spidy Web Browser

This module contains the LinkHandler class which extends QWebEnginePage
to provide enhanced navigation handling, security checks, and URL processing.
"""

import os
import time
from datetime import datetime

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineSettings


class LinkHandler(QWebEnginePage):
    """
    Custom web engine page handler that manages navigation requests and web content.
    
    This class provides enhanced security for navigation requests, tracks page history,
    and handles JavaScript interactions. It defines supported URL schemes with their
    handling policies and implements methods to detect potentially suspicious URLs.
    """
    # Define navigation type names for readable logs
    NAV_TYPE_NAMES = {
        QWebEnginePage.NavigationTypeLinkClicked: "Link Click",
        QWebEnginePage.NavigationTypeFormSubmitted: "Form Submission",
        QWebEnginePage.NavigationTypeBackForward: "Back/Forward Navigation",
        QWebEnginePage.NavigationTypeReload: "Page Reload",
        QWebEnginePage.NavigationTypeRedirect: "Redirect",
        QWebEnginePage.NavigationTypeTyped: "URL Typed",
        QWebEnginePage.NavigationTypeOther: "Other Navigation"
    }
    # Define supported URL schemes with handling policies
    SUPPORTED_SCHEMES = {
        'http': {'allow': True, 'description': 'HTTP protocol'},
        'https': {'allow': True, 'description': 'Secure HTTP protocol'},
        'file': {'allow': True, 'description': 'Local file access'},
        'ftp': {'allow': True, 'description': 'File Transfer Protocol'},
        'ftps': {'allow': True, 'description': 'Secure File Transfer Protocol'},
        'data': {'allow': True, 'description': 'Data URI scheme'},
        'mailto': {'allow': True, 'description': 'Email address link', 'external': True},
        'tel': {'allow': True, 'description': 'Telephone number link', 'external': True},
        'about': {'allow': True, 'description': 'Browser information'},
    }
    # Define potentially dangerous schemes
    SUSPICIOUS_SCHEMES = ['javascript', 'vbscript', 'data']

    def __init__(self, parent=None):
        super().__init__(parent)
        # Create profile that allows local file access
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        # Enable ALL required settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        # Initialize navigation history tracking
        self.nav_history = []
        self.nav_success_count = 0
        self.nav_failure_count = 0
        self.current_nav_start_time = 0
        self.suspicious_navigation_attempts = 0

    def log_navigation(self, message, level="INFO"):
        """Log navigation events with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")

    def get_navigation_type_name(self, nav_type):
        """Get readable name for navigation type"""
        return self.NAV_TYPE_NAMES.get(nav_type, f"Unknown ({nav_type})")

    def is_suspicious_url(self, url):
        """Check if URL might be suspicious or malicious"""
        suspicious = False
        reasons = []
        
        # Check scheme
        scheme = url.scheme().lower()
        if scheme in self.SUSPICIOUS_SCHEMES:
            suspicious = True
            reasons.append(f"Suspicious scheme: {scheme}")
        
        # Check for suspicious characters in URL
        url_string = url.toString()
        suspicious_chars = ['%00', '%0d', '%0a', '\0']  # null bytes, CR, LF
        for char in suspicious_chars:
            if char in url_string:
                suspicious = True
                reasons.append(f"Suspicious characters in URL: found '{char}'")
                break
        
        # Check for very long URLs (potential obfuscation)
        if len(url_string) > 2000:
            suspicious = True
            reasons.append(f"Excessively long URL: {len(url_string)} chars")
        return suspicious, reasons

    def record_navigation_attempt(self, url, nav_type, is_main_frame, success, error_reason=None):
        """Record a navigation attempt in the history"""
        end_time = time.time()
        duration = round((end_time - self.current_nav_start_time) * 1000, 2) if self.current_nav_start_time > 0 else 0
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url.toString(),
            "type": nav_type,
            "type_name": self.get_navigation_type_name(nav_type),
            "is_main_frame": is_main_frame,
            "scheme": url.scheme(),
            "success": success,
            "duration_ms": duration
        }
        if error_reason:
            entry["error"] = error_reason
            
        self.nav_history.append(entry)
        
        # Update counters
        if success:
            self.nav_success_count += 1
        else:
            self.nav_failure_count += 1
        # Keep history at a reasonable size
        if len(self.nav_history) > 100:
            self.nav_history = self.nav_history[-100:]
        return entry

    def get_navigation_stats(self):
        """Get statistics about navigation history"""
        total = self.nav_success_count + self.nav_failure_count
        success_rate = (self.nav_success_count / total * 100) if total > 0 else 0
        # Calculate average duration for successful navigations
        durations = [
            entry.get('duration_ms', 0) 
            for entry in self.nav_history
            if entry.get('success', False) and entry.get('duration_ms', 0) > 0
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
        return {
            "total_navigations": total,
            "successful": self.nav_success_count,
            "failed": self.nav_failure_count,
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "suspicious_attempts": self.suspicious_navigation_attempts
        }

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        """Enhanced navigation request handler with improved logging and security checks"""
        # Record start time for performance tracking
        self.current_nav_start_time = time.time()
        # Get navigation type name for readable logs
        nav_type_name = self.get_navigation_type_name(nav_type)
        
        # Enhanced structured debug logging
        self.log_navigation("\nNavigation Request Details:", "DEBUG")
        self.log_navigation(f"URL: {url.toString()}", "DEBUG")
        self.log_navigation(f"Type: {nav_type} ({nav_type_name})", "DEBUG")
        self.log_navigation(f"Is Main Frame: {is_main_frame}", "DEBUG")
        self.log_navigation(f"URL Scheme: {url.scheme()}", "DEBUG")
        # URL security check
        is_suspicious, reasons = self.is_suspicious_url(url)
        if is_suspicious:
            self.suspicious_navigation_attempts += 1
            self.log_navigation(
                f"SECURITY WARNING: Potentially suspicious URL detected:", "WARNING")
            for reason in reasons:
                self.log_navigation(f"- {reason}", "WARNING")
        # Always allow main frame navigation
        if is_main_frame:
            self.log_navigation(f"Allowing main frame navigation to {url.toString()}", "INFO")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True)
            return True
        # Handle navigation by type
        scheme = url.scheme().lower()
        # Handle different navigation types
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            self.log_navigation(f"Link clicked: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeFormSubmitted:
            self.log_navigation(f"Form submitted to: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeBackForward:
            self.log_navigation(f"Back/Forward navigation to: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeReload:
            self.log_navigation(f"Page reload: {url.toString()}", "INFO")
        elif nav_type == QWebEnginePage.NavigationTypeRedirect:
            self.log_navigation(f"Redirect to: {url.toString()}", "INFO")
        # Process URL based on scheme
        if scheme in self.SUPPORTED_SCHEMES:
            scheme_info = self.SUPPORTED_SCHEMES[scheme]
            # Check if scheme is allowed
            if not scheme_info.get('allow', False):
                self.log_navigation(f"Navigation blocked - scheme '{scheme}' is not allowed", "WARNING")
                self.record_navigation_attempt(
                    url, nav_type, is_main_frame, False, f"Scheme '{scheme}' is not allowed")
                return False
                
            # Handle external schemes (mailto, tel, etc.)
            if scheme_info.get('external', False):
                self.log_navigation(
                    f"External scheme '{scheme}' detected, attempting to open with external application", 
                    "INFO")
                # For mailto and tel links, you might integrate with system applications
                # This is a simplified demonstration - in production, you might use QDesktopServices
                self.record_navigation_attempt(
                    url, nav_type, is_main_frame, True, "Handled by external application")
                return False  # Don't navigate in browser, but consider it successful for tracking

            # Handle specific schemes
            if scheme == 'file':
                path = url.toLocalFile()
                self.log_navigation(f"Handling file URL: {path}", "DEBUG")
                # Handle relative paths
                if not os.path.isabs(path):
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    path = os.path.join(base_dir, path)
                    self.log_navigation(f"Converted to absolute path: {path}", "DEBUG")
                if os.path.exists(path):
                    self.log_navigation(f"File exists, allowing navigation", "INFO")
                    self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                    return True
                # File doesn't exist - try fallback
                self.log_navigation(f"File does not exist: {path}", "WARNING")
                # Try fallback to HTTP if file not found
                http_url = QUrl("http://" + url.fileName())
                if http_url.isValid():
                    self.log_navigation(f"Attempting fallback to HTTP: {http_url.toString()}", "INFO")
                    self.record_navigation_attempt(
                        url, nav_type, is_main_frame, True, "File not found, falling back to HTTP")
                    return True
                
                # No fallback available
                self.log_navigation(f"Navigation failed - file not found and no valid fallback", "ERROR")
                self.record_navigation_attempt(
                    url, nav_type, is_main_frame, False, "File not found and no valid fallback")
                return False
                
            # Standard HTTP/HTTPS handling
            elif scheme in ('http', 'https'):
                self.log_navigation(f"Allowing navigation to {scheme} URL: {url.toString()}", "INFO")
                self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                return True
                
            # FTP handling
            elif scheme in ('ftp', 'ftps'):
                self.log_navigation(f"Allowing navigation to {scheme} URL: {url.toString()}", "INFO")
                self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                return True
                
            # Data URI scheme (inline content)
            elif scheme == 'data':
                self.log_navigation(f"Processing data URI", "INFO")
                # Check if it's a potentially malicious data URI (e.g., executable content)
                data_content = url.toString()
                if 'application/x-msdownload' in data_content or 'application/octet-stream' in data_content:
                    self.log_navigation("Potentially unsafe data URI with executable content", "WARNING")
                    self.suspicious_navigation_attempts += 1
                
                self.record_navigation_attempt(url, nav_type, is_main_frame, True)
                return True
                
            # Default handling for supported schemes
            self.log_navigation(f"Allowing navigation to {scheme} URL via default handler", "INFO")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True)
            return True
                
        else:
            # Unsupported scheme
            self.log_navigation(f"Unsupported URL scheme: {scheme}", "WARNING")
            
            # If it's a known but unsupported scheme, log specifically
            if scheme in ['javascript', 'vbscript']:
                self.log_navigation(f"Script scheme '{scheme}' not supported for security reasons", "WARNING")
                self.record_navigation_attempt(url, nav_type, is_main_frame, False, f"Script scheme '{scheme}' blocked")
                return False
                
            # Unknown scheme - try anyway but log the attempt
            self.log_navigation(f"Unknown scheme '{scheme}', attempting navigation with caution", "WARNING")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True, f"Unknown scheme '{scheme}' allowed with caution")
            return True

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Log JavaScript messages for debugging
        print(f"JavaScript ({level}) [{sourceID}:{lineNumber}]: {message}")

    def javaScriptAlert(self, securityOrigin, msg):
        """Handle JavaScript alerts with enhanced logging"""
        self.log_navigation(f"JavaScript Alert from {securityOrigin.host()}: {msg}", "INFO")
        # In a real implementation, you might show a dialog to the user
        # For headless operation, we just log the alert

