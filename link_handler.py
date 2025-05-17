"""
Link Handler for Spidy Web Browser

This module contains the LinkHandler class which extends QWebEnginePage
to provide enhanced navigation handling, security checks, and URL processing.
"""

import os
import time
import urllib.parse
from datetime import datetime
import markdown
import logging
import re

from PyQt6.QtCore import QUrl, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel

try:
    from html_cleaner import HTMLCleaner
    HTML_CLEANER_AVAILABLE = True
except ImportError:
    HTML_CLEANER_AVAILABLE = False


class LinkHandler(QWebEnginePage):
    """
    Custom web engine page handler that manages navigation requests and web content.
    
    This class provides enhanced security for navigation requests, tracks page history,
    and handles JavaScript interactions. It defines supported URL schemes with their
    handling policies and implements methods to detect potentially suspicious URLs.
    """
    # Signal for opening URLs in new tabs
    open_url_in_new_tab = pyqtSignal(QUrl)
    # Signal to indicate when debugging is needed for link clicks
    link_click_debug = pyqtSignal(str, str)
    # Signal emitted when a link is clicked in a page with base target="_blank"
    link_clicked_new_tab = pyqtSignal(str, str)  # href, target attribute
    # Define navigation type names for readable logs
    NAV_TYPE_NAMES = {
        QWebEnginePage.NavigationType.NavigationTypeLinkClicked: "Link Click",
        QWebEnginePage.NavigationType.NavigationTypeFormSubmitted: "Form Submission",
        QWebEnginePage.NavigationType.NavigationTypeBackForward: "Back/Forward Navigation",
        QWebEnginePage.NavigationType.NavigationTypeReload: "Page Reload",
        QWebEnginePage.NavigationType.NavigationTypeRedirect: "Redirect",
        QWebEnginePage.NavigationType.NavigationTypeTyped: "URL Typed",
        QWebEnginePage.NavigationType.NavigationTypeOther: "Other Navigation"
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
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        # Enable ALL required settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        
        # Setup HTML cleaner if available
        self.html_cleaner = HTMLCleaner() if HTML_CLEANER_AVAILABLE else None
        
        # Pre-configure JavaScript polyfills and page monitoring
        self.loadStarted.connect(self._inject_polyfills)
        self.loadFinished.connect(self._check_for_base_tag)
        self.loadFinished.connect(self._inject_link_handlers)
        self.loadFinished.connect(self._setup_web_channel)
        
        # Initialize navigation history tracking
        self.navigation_history = []
        self.nav_success_count = 0
        self.nav_failure_count = 0
        self.current_nav_start_time = 0
        self.suspicious_navigation_attempts = 0
        # Signal for handling special URL loading after navigation
        self.pending_data_url = None
        
        # Store base tag information
        self.has_base_tag = False
        self.base_target = None
        
        # Configure logging
        self.logger = logging.getLogger('spidy.link_handler')
        
        # Store the original javaScriptConsoleMessage method before overriding
        self._original_js_console_handler = self.javaScriptConsoleMessage
        
        # Handle JavaScript communication
        self.javaScriptConsoleMessage = self._enhanced_js_console_handler
        
        # Set up the web channel for JavaScript-Python communication
        self.web_channel = QWebChannel(self)
        self.web_channel.registerObject("pyObject", self)
        self.setWebChannel(self.web_channel)
        
    def _inject_polyfills(self):
        """Inject required JavaScript polyfills"""
        polyfills = """
            // String.replaceAll polyfill
            if (!String.prototype.replaceAll) {
                String.prototype.replaceAll = function(str, newStr) {
                    // If a regex pattern
                    if (Object.prototype.toString.call(str).toLowerCase() === '[object regexp]') {
                        return this.replace(str, newStr);
                    }
                    // If a string
                    return this.replace(new RegExp(str.replace(/[.*+?^${}()|[\\\\]\\\\]/g, '\\\\$&'), 'g'), newStr);
                };
            }
            
            // Add bokeh-specific error handling
            window.addEventListener('error', function(event) {
                if (event.message && event.message.includes('replaceAll')) {
                    console.log('[Spidy Browser] Caught replaceAll error, polyfill should handle it');
                }
            });
            
            // Define global namespace for Spidy Browser utilities
            window.SpidyBrowser = {
                _linkHandlersInstalled: false,
                _baseTargetFound: false,
                _baseTarget: null,
                
                // Methods for link handling
                notifyLinkClick: function(href, targetAttr) {
                    // This function will be called by our event handlers
                    console.log('[Spidy Browser] Link clicked:', href, 'target:', targetAttr);
                    
                    // Create custom event for Python to intercept
                    const event = new CustomEvent('spidy-link-clicked', {
                        detail: {
                            href: href,
                            target: targetAttr || '_self'
                        }
                    });
                    document.dispatchEvent(event);
                    return true;
                }
            };
            
            // Create globally accessible function for Python to call
            window.checkBaseTags = function() {
                const baseElements = document.getElementsByTagName('base');
                if (baseElements.length > 0) {
                    const baseElement = baseElements[0];
                    const targetAttr = baseElement.getAttribute('target');
                    
                    window.SpidyBrowser._baseTargetFound = true;
                    window.SpidyBrowser._baseTarget = targetAttr;
                    
                    return {
                        found: true,
                        target: targetAttr,
                        href: baseElement.getAttribute('href')
                    };
                }
                return { found: false };
            };
            
        """
        
    def _check_for_base_tag(self, ok):
        """Check if page has a base tag with target attribute"""
        if not ok:
            return
            
        script = """
        (function() {
            let baseEl = document.querySelector('base');
            if (baseEl) {
                return {
                    found: true,
                    target: baseEl.getAttribute('target'),
                    href: baseEl.getAttribute('href')
                };
            }
            return { found: false };
        })();
        """
        
        def handle_base_result(result):
            if result and result.get('found', False):
                self.has_base_tag = True
                self.base_target = result.get('target')
                self.log_navigation(f"Detected <base> tag with target='{self.base_target}'", "INFO")
                
                # Add debug JavaScript if we detected a base tag with target="_blank"
                if self.base_target == "_blank":
                    self._inject_link_debug_script()
            else:
                self.has_base_tag = False
                self.base_target = None
                
        self.runJavaScript(script, 0, handle_base_result)
        
        # Additional web channel setup script
        script = """
        if (!window.pyObjectReadyCallbacks) {
            window.pyObjectReadyCallbacks = [];
        }
        
        // Helper function to ensure pyObject is available
        window.whenPyObjectReady = function(callback) {
            if (window.pyObject) {
                callback(window.pyObject);
            } else {
                window.pyObjectReadyCallbacks.push(callback);
            }
        };
        """
        self.runJavaScript(script)
    
    @pyqtSlot(str, str)
    def onLinkNewTab(self, href, target):
        """
        Handle link clicks that should open in a new tab
        
        Args:
            href (str): The href attribute of the clicked link
            target (str): The target attribute of the clicked link
        """
        self.log_navigation(f"Python handler called for new tab link: {href} with target={target}", "INFO")
        # Emit the signal for the tab manager to handle
        self.link_clicked_new_tab.emit(href, target)
    
    @pyqtSlot(str, str, str)
    def onWindowOpen(self, url, target, features):
        """
        Handle window.open() calls that should open in a new tab/window
        
        Args:
            url (str): The URL to open
            target (str): The target window name
            features (str): Window features string
        """
        self.log_navigation(f"Python handler called for window.open: {url} with target={target}", "INFO")
        # For _blank targets, emit the signal to open in a new tab
        if target == "_blank":
            self.link_clicked_new_tab.emit(url, target)
    
    def _inject_link_handlers(self, ok):
        """
        Inject JavaScript to handle link clicks with proper target attribute support
        
        Args:
            ok (bool): Whether the page loaded successfully
        """
        if not ok:
            return
            
        # Skip if page didn't load properly
        script = """
        (function() {
            // Don't re-install if already installed
            if (window.SpidyBrowser && window.SpidyBrowser._linkHandlersInstalled) {
                console.log('[Spidy Browser] Link handlers already installed');
                return;
            }
            
            // Setup global namespace if needed
            if (!window.SpidyBrowser) {
                window.SpidyBrowser = {
                    _linkHandlersInstalled: false,
                    _baseTargetFound: false,
                    _baseTarget: null
                };
            }
            
            // Check for base tag
            const baseElements = document.getElementsByTagName('base');
            if (baseElements.length > 0) {
                const baseEl = baseElements[0];
                const targetAttr = baseEl.getAttribute('target');
                
                window.SpidyBrowser._baseTargetFound = true;
                window.SpidyBrowser._baseTarget = targetAttr;
                
                console.log('[Spidy Browser] Found base tag with target:', targetAttr);
            }
            
            // Handle link clicks with target attributes
            document.addEventListener('click', function(event) {
                let target = event.target;
                
                // Find the closest link
                while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                }
                
                // End of the click event handler
            });
            
            console.log('[Spidy Browser] Link handlers installed successfully');
            window.SpidyBrowser._linkHandlersInstalled = true;
        })();
        """
        self.runJavaScript(script)


    def _setup_web_channel(self, ok):
        """
        Set up the web channel for JavaScript-Python communication
        
        Args:
            ok (bool): Whether the page loaded successfully
        """
        if not ok:
            return

        try:
            # Read qwebchannel.js file from the project directory
            with open('/home/juren/Projects/Spidy/qwebchannel.js', 'r') as f:
                qwebchannel_js = f.read()

            def on_qwebchannel_loaded(result):
                setup_script = """
                window.onload = function() {
                    console.log('[Spidy Browser] Executing QWebChannel setup');
                    if (typeof QWebChannel !== 'undefined') {
                        new QWebChannel(qt.webChannelTransport, function(channel) {
                            window.pyObject = channel.objects.pyObject;
                            console.log('[Spidy Browser] QWebChannel initialized');
                            document.addEventListener('click', function(event) {
                                let target = event.target;
                                while (target && target.tagName !== 'A') {
                                    target = target.parentElement;
                                }
                                if (target && target.tagName === 'A') {
                                    const href = target.getAttribute('href');
                                    const targetAttr = target.getAttribute('target');
                                    if (targetAttr === '_blank' || 
                                        (document.querySelector('base[target="_blank"]') && !targetAttr)) {
                                        event.preventDefault();
                                        if (window.pyObject && window.pyObject.onLinkNewTab) {
                                            window.pyObject.onLinkNewTab(href, '_blank');
                                            return false;
                                        }
                                    }
                                }
                            });
                        });
                    } else {
                        console.error('[Spidy Browser] QWebChannel undefined after expected setup');
                    }
                }
                """
                self.runJavaScript(setup_script)

            # Load qwebchannel.js first and log loading attempt
            self.runJavaScript(qwebchannel_js, on_qwebchannel_loaded)

        except Exception as e:
            print(f"Error loading qwebchannel.js: {e}. Ensure the file exists and is accessible by the Spidy browser.")
        
    def _inject_link_debug_script(self):
        """Inject JavaScript to help debug link clicks with base target"""
        debug_script = """
        (function() {
            // Override window.open for better link handling
            const originalWindowOpen = window.open;
            window.open = function(url, target, features) {
                console.log('[Spidy Browser] window.open called:', url, target, features);
                
                // Call the original, but also notify our custom handler
                if (window.spidyLinkHandler) {
                    window.spidyLinkHandler(url, target || '_blank');
                }
                
                return originalWindowOpen.apply(this, arguments);
            };
            
            // Create a custom link handler for Spidy
            window.spidyLinkHandler = function(url, target) {
                // Create a custom event that will be picked up by our QWebChannel
                const event = new CustomEvent('spidy-link-clicked', {
                    detail: {
                        url: url,
                        target: target
                    }
                });
                document.dispatchEvent(event);
                
                console.log('[Spidy Browser] Custom link handler called:', url, target);
                return true;
            };
            
            // Monitor all link clicks
            document.addEventListener('click', function(e) {
                let target = e.target;
                while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                }
                
                if (target && target.tagName === 'A') {
                    const href = target.getAttribute('href');
                    const targetAttr = target.getAttribute('target') || '_self';
                    
                    console.log('[Spidy Browser] Link clicked:', href, 'target:', targetAttr);
                    
                    // If this is a blank target link, use our custom handler
                    if (targetAttr === '_blank' || document.querySelector('base[target="_blank"]')) {
                        // Prevent the default action
                        e.preventDefault();
                        
                        // Use our custom handler
                        if (window.spidyLinkHandler) {
                            window.spidyLinkHandler(href, targetAttr);
                        }
                    }
                }
            }, true);
            
            console.log('[Spidy Browser] Link debug handler installed');
        })();
        """
        self.runJavaScript(debug_script)

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
            "navigation_type": str(nav_type),
            "is_main_frame": is_main_frame,
            "success": success,
            "error_reason": error_reason,
            "duration_ms": duration
        }
        self.navigation_history.append(entry)

    def createWindow(self, _type):
        """
        Handle requests to open a new tab or window (e.g., target="_blank" or window.open).
        This allows context menu actions like 'Open Link in New Tab' to work.
        """
        parent_browser = self.parent()
        if hasattr(parent_browser, "browser"):
            return parent_browser.browser.tab_manager.add_new_tab_page()
        return super().createWindow(_type)

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

    def check_link_target(self, url):
        """Check if a link has a target attribute like _blank"""
        script = """
        (function() {
            // Try to find the link with this URL in the document
            const links = document.querySelectorAll('a[href="' + arguments[0] + '"]');
            if (links.length > 0) {
                return {
                    found: true,
                    href: links[0].getAttribute('href'),
  
                  target: links[0].getAttribute('target') || '_self',
                    hasBaseTag: !!document.querySelector('base[target]'),
                    baseTarget: document.querySelector('base[target]') ? 
                                document.querySelector('base[target]').getAttribute('target') : null
                };
            }
            return { found: false };
        })();
        """
        
        def handle_link_info(result):
            if result and result.get('found', False):
                target = result.get('target', '_self')
                if target == '_blank' or (result.get('hasBaseTag', False) and result.get('baseTarget') == '_blank'):
                    self.log_navigation(f"Link with target='{target}' should open in new tab", "INFO")
                    # Emit signal to open in new tab
                    self.open_url_in_new_tab.emit(url)
        
        self.runJavaScript(script, 0, handle_link_info, url.toString())
    
    def _enhanced_js_console_handler(self, level, message, line_number, source_id):
        """Enhanced handler for JavaScript console messages"""
        # Process spidy-link-clicked events
        if "spidy-link-clicked" in message or "Link clicked" in message:
            self.log_navigation(f"Link event: {message}", "DEBUG")
            
        # Call the original handler, not this method (which would cause recursion)
        self._original_js_console_handler(level, message, line_number, source_id)
    
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
        self.log_navigation(f"Has base tag: {self.has_base_tag}, target: {self.base_target}", "DEBUG")
        
        # Handle our custom spidy-md:// protocol for Markdown navigation
        if url.scheme() == 'spidy-md':
            self.log_navigation(f"Detected spidy-md protocol for Markdown navigation", "INFO")
            # Extract the original file URL from our custom URL
            encoded_path = url.toString().replace('spidy-md://', '')
            self.log_navigation(f"Encoded path from spidy-md URL: '{encoded_path}'", "DEBUG")
            
            if not encoded_path:
                self.log_navigation("Error: Empty encoded path in spidy-md URL", "ERROR")
                return False
                
            # Decode the URL-encoded path
            original_file_url = urllib.parse.unquote(encoded_path)
            self.log_navigation(f"Decoded original Markdown file URL: '{original_file_url}'", "INFO")
            
            # Handle file URLs properly
            if not original_file_url.startswith('file://'):
                # If it's a relative path, convert to absolute file URL
                if not original_file_url.startswith('/'):
                    # Get current page URL as base
                    current_url = self.url().toString()
                    self.log_navigation(f"Current URL for base reference: {current_url}", "DEBUG")
                    
                    # Extract base directory from current URL
                    if current_url.startswith('file://'):
                        base_dir = os.path.dirname(QUrl(current_url).toLocalFile())
                        self.log_navigation(f"Base directory for relative path: {base_dir}", "DEBUG")
                        
                        # Combine base path with relative path
                        absolute_path = os.path.normpath(os.path.join(base_dir, original_file_url))
                        original_file_url = f"file://{absolute_path}"
                        self.log_navigation(f"Resolved absolute file URL: {original_file_url}", "DEBUG")
                    else:
                        # Not a file URL, prefix with file:// protocol
                        original_file_url = f"file://{original_file_url}"
                else:
                    # Absolute path but missing file:// protocol
                    original_file_url = f"file://{original_file_url}"
            
            # Create a proper QUrl object and redirect to it
            file_url = QUrl(original_file_url)
            if file_url.isValid():
                self.log_navigation(f"Redirecting to Markdown file: {file_url.toString()}", "INFO")
                # This will trigger another navigation request to the actual file URL
                # which will be handled by our normal Markdown processing logic
                self.setUrl(file_url)
                return False  # Cancel this navigation, we're redirecting
            else:
                self.log_navigation(f"Invalid Markdown file URL: {original_file_url}", "ERROR")
                return False
        # URL security check
        is_suspicious, reasons = self.is_suspicious_url(url)
        if is_suspicious:
            self.suspicious_navigation_attempts += 1
            self.log_navigation(f"SECURITY WARNING: Potentially suspicious URL detected:", "WARNING")
            for reason in reasons:
                self.log_navigation(f"- {reason}", "WARNING")
        
        # Get the URL scheme for handling
        scheme = url.scheme().lower()
        
        # Special case for main frame navigation to Markdown files
        if is_main_frame and scheme == 'file' and url.toString().lower().endswith('.md'):
            self.log_navigation(f"Main frame navigation to Markdown file: {url.toString()}", "INFO")
            path = url.toLocalFile()
            if os.path.exists(path):
                self.log_navigation(f"Markdown file exists, will process it", "INFO")
                try:
                    # Process the Markdown file
                    self.log_navigation(f"Starting Markdown conversion for main frame: {path}", "DEBUG")
                    html_content = self.convert_markdown_to_html(path)
                    self.log_navigation(f"Main frame Markdown conversion completed, HTML size: {len(html_content)} bytes", "DEBUG")
                    
                    # URL encode the HTML content for the data URL (important for proper rendering)
                    encoded_html = urllib.parse.quote(html_content, safe='')
                    self.log_navigation(f"HTML content encoded for data URL", "DEBUG")
                    
                    # Create a data URL with the encoded HTML content
                    data_url = QUrl(f"data:text/html;charset=utf-8,{encoded_html}")
                    self.log_navigation(f"Created data URL for Markdown content", "DEBUG")
                    
                    # Use loadFinished signal to load the data URL after this handler returns
                    # Create a unique handler function to avoid multiple connections
                    def load_data_url_handler(ok, url=data_url):
                        # Disconnect this handler immediately to prevent accumulation
                        self.loadFinished.disconnect(load_data_url_handler)
                        if ok:
                            self.setUrl(url)
                    
                    # Connect our handler function
                    self.loadFinished.connect(load_data_url_handler)
                    
                    self.record_navigation_attempt(url, nav_type, is_main_frame, True, "Markdown file detected, will convert to HTML")
                    return True  # Let navigation proceed, but we'll replace with data URL when loaded
                except Exception as e:
                    import traceback
                    self.log_navigation(f"Error converting Markdown in main frame handler: {str(e)}", "ERROR")
                    self.log_navigation(f"Exception traceback: {traceback.format_exc()}", "ERROR")
                    # Fall through to regular handling
        
        # Always allow main frame navigation (for other cases)
        if is_main_frame:
            self.log_navigation(f"Allowing main frame navigation to {url.toString()}", "INFO")
            self.record_navigation_attempt(url, nav_type, is_main_frame, True)
            return True
        # Handle different navigation types
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            self.log_navigation(f"Link clicked: {url.toString()}", "INFO")
            
            # Check if this link should open in a new tab because of <base target="_blank">
            if self.has_base_tag and self.base_target == "_blank":
                self.log_navigation(f"Link should open in new tab due to <base target=\"_blank\">", "INFO")
                self.open_url_in_new_tab.emit(url)
                return False  # Block this navigation request since we're opening in a new tab
                
            # Run a JavaScript check for link target
            self.check_link_target(url)
                
        elif nav_type == QWebEnginePage.NavigationType.NavigationTypeFormSubmitted:
            self.log_navigation(f"Form submitted to {url.toString()}", "INFO")
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
                # Debug the file path
                self.log_navigation(f"Checking file path: {path}", "DEBUG")
                self.log_navigation(f"File exists? {os.path.exists(path)}", "DEBUG")
                
                if os.path.exists(path):
                    self.log_navigation(f"File exists, allowing navigation", "INFO")
                    
                    # For non-main frame, don't try to process Markdown (already handled in main frame handler)
                    if not is_main_frame and path.lower().endswith('.md'):
                        self.log_navigation(f"Non-main frame Markdown file detected but skipping special handling: {path}", "DEBUG")
                    
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
        """Handle JavaScript console messages with enhanced logging and filtering"""
        # Map numeric levels to readable names
        level_names = {
            0: "INFO",
            1: "WARNING",
            2: "ERROR"
        }
        level_name = level_names.get(level, f"LEVEL{level}")
        
        filename = sourceID.split('/')[-1] if sourceID else 'unknown'
        
        # Filter out common and repetitive messages
        ignore_patterns = [
            "[Spidy Browser] Polyfills injected successfully",
            "Uncaught TypeError: Cannot read property",
            "Uncaught ReferenceError: replaceAll",
            "wasm-unsafe-eval",
            "Failed to delete the database: Database IO error"
        ]
        
        should_log = True
        for pattern in ignore_patterns:
            if pattern in message:
                should_log = False
                break
        
        # Only log if the message passes our filter
        if should_log:
            # Format message for better readability
            if "bokeh" in sourceID.lower():
                self.log_navigation(f"Bokeh {level_name}: {message} (in {filename}:{lineNumber})", level_name)
            else:
                self.log_navigation(f"JavaScript {level_name}: {message} (in {filename}:{lineNumber})", level_name)
    
    def javaScriptAlert(self, securityOrigin, msg):
        """Handle JavaScript alerts with enhanced logging"""
        self.log_navigation(f"JavaScript Alert from {securityOrigin.host()}: {msg}", "INFO")
        # In a real implementation, you might show a dialog to the user
        # For headless operation, we just log the alert

    def javaScriptLoadFinished(self, ok):
        """Handle JavaScript load completion"""
        if ok:
            self.log_navigation("JavaScript load completed successfully", "DEBUG")
            
            # Check if we have a pending data URL to load (for Markdown conversion)
            if self.pending_data_url is not None:
                self.log_navigation(f"Loading pending data URL after JavaScript load", "DEBUG")
                data_url = self.pending_data_url
                self.pending_data_url = None
                self.setUrl(data_url)
        else:
            self.log_navigation("JavaScript load failed", "WARNING")


    def convert_markdown_to_html(self, markdown_path):
        """
        Convert Markdown file content to HTML with proper styling.
        
        Args:
            markdown_path (str): Path to the Markdown file
            
        Returns:
            str: HTML content with styling
        """
        self.log_navigation(f"Reading Markdown file: {markdown_path}", "DEBUG")
        
        # Read the Markdown file
        with open(markdown_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Get the directory of the Markdown file for resolving relative links
        base_dir = os.path.dirname(markdown_path)
        
        # Convert Markdown to HTML with the Python-Markdown library
        html_body = markdown.markdown(
            md_content,
            extensions=['extra', 'tables', 'toc', 'fenced_code', 'codehilite']
        )
        
        # Include the base directory for proper relative path resolution
        # Ensure the base directory path is properly URL-encoded
        encoded_base_dir = urllib.parse.quote(base_dir)
        base_tag = f'<base href="file://{encoded_base_dir}/">'
        self.log_navigation(f"Set base tag: {base_tag}", "DEBUG")
        
        # Get the filename for the title
        title = os.path.basename(markdown_path)
        
        # Prepare the complete HTML with styling
        # Create the HTML template first without f-string to avoid issues with '#' characters
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {base_tag}
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background-color: #fff;
            /* Improve rendering performance */
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
            will-change: transform;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
    </style>
    <script>
        // Ensure all links work correctly by intercepting clicks and handling navigation
        document.addEventListener('DOMContentLoaded', function() {{
            // Handle link clicks
            document.body.addEventListener('click', function(event) {{
                // Find the closest anchor element
                let target = event.target;
                while (target && target.tagName !== 'A') {{
                    target = target.parentElement;
                }}
                
                // If we clicked on a link
                if (target && target.tagName === 'A') {{
                    let href = target.getAttribute('href');
                    
                    // Handle relative links - combine with base href
                    if (href && !href.match(/^(https?:|file:|data:|mailto:|tel:|#)/i)) {{
                        // Get the base URL
                        let baseElement = document.querySelector('base');
                        let baseHref = baseElement ? baseElement.getAttribute('href') : '';
                        
                        // If it's not an absolute URL and doesn't start with /, it's relative to current path
                        if (baseHref && !href.startsWith('/')) {{
                            // Ensure baseHref ends with / for proper path joining
                            if (!baseHref.endsWith('/')) {{
                                baseHref += '/';
                            }}
                            href = baseHref + href;
                        }}
                        
                        // Check if this is a Markdown file link
                        if (href.toLowerCase().endsWith('.md')) {{
                            // Make sure we have a complete URL for the Markdown file
                            let fullUrl = href;
                            
                            // If it's a relative path (no protocol)
                            if (!href.match(/^[a-z]+:/i)) {{
                                // If it doesn't start with /, prepend current directory
                                if (!href.startsWith('/')) {{
                                    let currentPath = window.location.pathname;
                                    let currentDir = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
                                    fullUrl = currentDir + href;
                                    console.log('[Spidy Browser] Resolved relative URL to: ' + fullUrl);
                                }}
                                
                                // Add file:// protocol if missing
                                if (!fullUrl.startsWith('file://')) {{
                                    fullUrl = 'file://' + fullUrl;
                                    console.log('[Spidy Browser] Added file protocol: ' + fullUrl);
                                }}
                            }}
                            
                            // Use a special protocol to signal we want to navigate to another markdown file
                            let encodedUrl = encodeURIComponent(fullUrl);
                            let spidyMdUrl = 'spidy-md://' + encodedUrl;
                            console.log('[Spidy Browser] Created spidy-md URL: ' + spidyMdUrl);
                            
                            window.location.href = spidyMdUrl;
                            event.preventDefault();
                        }} else {{
                            // For non-markdown files, use standard navigation
                            window.location.href = href;
                            event.preventDefault();
                        }}
                    }}
                    // Handle fragment links within page
                    else if (href && href.charAt(0) === String.fromCharCode(35)) {{
                        // Get the target element
                        let targetElement = document.getElementById(href.substring(1));
                        if (targetElement) {{
                            targetElement.scrollIntoView({{behavior: 'smooth'}}); 
                            event.preventDefault();
                        }}
                    }}
                }}
            }});
            
            // Add visible focus state to improve accessibility
            const style = document.createElement('style');
            style.textContent = `
                a:focus {{
                    outline: 2px solid #0366d6;
                    outline-offset: 2px;
                }}
            `;
            document.head.appendChild(style);
        }});
    </script>
</head>
<body>
    <article class="markdown-body">
        {html_body}
    </article>
</body>
</html>
"""
        # Now apply the formatting after the template is defined
        html = html_template.format(
            base_tag=base_tag,
            title=title,
            html_body=html_body
        )
        return html
