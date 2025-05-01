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
        # Pre-configure JavaScript polyfills
        self.loadStarted.connect(self._inject_polyfills)
        
        # Initialize navigation history tracking
        self.nav_history = []
        self.nav_success_count = 0
        self.nav_failure_count = 0
        self.current_nav_start_time = 0
        self.suspicious_navigation_attempts = 0
        # Signal for handling special URL loading after navigation
        self.pending_data_url = None
        
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
            
            // Notify when polyfills are loaded
            console.log('[Spidy Browser] Polyfills injected successfully');
        """
        self.runJavaScript(polyfills)

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
