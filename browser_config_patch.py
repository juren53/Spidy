"""
This is a partial update for browser.py to add ConfigManager integration.
Apply these changes to the existing browser.py file.
"""

# Add to imports section:
from config_manager import get_config

# Modify Browser.__init__ method:
def __init__(self):
    super().__init__()
    
    # Get the configuration manager
    self.config = get_config()
    
    # Initialize configuration directory
    self.config_dir = self.config.config_dir
    if not os.path.exists(self.config_dir):
        os.makedirs(self.config_dir)
        
    # Create cache directory if specified
    cache_dir = self.config.get("General", "cache_dir", "")
    if not cache_dir:
        cache_dir = os.path.join(self.config_dir, "cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Create central widget
    self.central_widget = QWidget()
    self.setCentralWidget(self.central_widget)

    # Initialize manager classes
    self.tab_manager = TabManager(self)
    self.navigation_manager = NavigationManager(self)
    self.bookmark_manager = BookmarkManager(self)
    self.statistics_manager = StatisticsManager(self)
    self.ui_manager = UIManager(self)

    # Configure initial settings
    self._configure_browser_settings()
    
    # Create initial tab with configured home page
    home_page = self.config.get("General", "home_page", "https://search.brave.com/")
    self.tab_manager.add_new_tab(QUrl(home_page))
    
    self.show()

# Add new method to Browser class:
def _configure_browser_settings(self):
    """Configure browser settings based on config.ini values"""
    # Get the default profile
    profile = QWebEngineProfile.defaultProfile()
    
    # Set custom user agent if provided
    user_agent = self.config.get("Browser", "user_agent", "")
    if user_agent:
        profile.setHttpUserAgent(user_agent)
        
    # Configure privacy settings
    if self.config.get_boolean("Privacy", "block_third_party_cookies", True):
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
    # Configure JavaScript
    settings = profile.settings()
    js_enabled = self.config.get_boolean("Browser", "javascript_enabled", True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, js_enabled)
    
    # Configure WebGL
    webgl_enabled = self.config.get_boolean("Rendering", "webgl_enabled", False)
    settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, webgl_enabled)
    
    # Configure proxy if enabled
    if self.config.get_boolean("Network", "proxy_enabled", False):
        proxy_host = self.config.get("Network", "proxy_host", "")
        proxy_port = self.config.get("Network", "proxy_port", "")
        proxy_type = self.config.get("Network", "proxy_type", "http")
        
        if proxy_host and proxy_port:
            from PyQt6.QtNetwork import QNetworkProxy
            proxy = QNetworkProxy()
            
            if proxy_type.lower() == "socks5":
                proxy.setType(QNetworkProxy.ProxyType.Socks5Proxy)
            else:
                proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
                
            proxy.setHostName(proxy_host)
            proxy.setPort(int(proxy_port))
            QNetworkProxy.setApplicationProxy(proxy)

# Modify closeEvent method to save config:
def closeEvent(self, event):
    """Handle application close event"""
    self.navigation_manager.save_history()
    self.bookmark_manager.save_bookmarks()
    
    # Also save any modified configuration
    self.config.save_config()
    
    super().closeEvent(event)

# Add new methods to Browser class for configuration management:
def show_config(self):
    """Show configuration dialog"""
    config_dialog = QDialog(self)
    config_dialog.setWindowTitle("Spidy Configuration")
    config_dialog.resize(600, 450)

    layout = QVBoxLayout()
    layout.addWidget(QLabel("<h2>Spidy Browser Configuration</h2>"))
    
    # Display current configuration
    config_text = f"""
    <h3>Current Configuration</h3>
    <pre style="background-color: #f5f5f5; padding: 10px; font-family: monospace;">
{self.config}
    </pre>
    
    <h3>Environment Variables</h3>
    <p>The following environment variables are currently affecting the browser:</p>
    """
    
    env_vars = self.config.get_environment_vars()
    if env_vars:
        config_text += "<ul>"
        for var, value in env_vars.items():
            config_text += f"<li><b>{var}</b> = {value}</li>"
        config_text += "</ul>"
    else:
        config_text += "<p><i>No Spidy environment variables are set.</i></p>"
    
    config_text += """
    <h3>Configuration File</h3>
    <p>Edit the configuration file at:</p>
    <pre style="background-color: #f5f5f5; padding: 5px; font-family: monospace;">~/.spidy/config.ini</pre>
    
    <h3>Configuration Options</h3>
    <p>You can configure Spidy in three ways:</p>
    <ol>
        <li>Edit the config.ini file</li>
        <li>Set environment variables with the SPIDY_ prefix</li>
        <li>Use command line arguments in the format --section.option=value</li>
    </ol>
    
    <p>For example, to enable software rendering:</p>
    <ul>
        <li>In config.ini: <code>use_software_rendering = True</code> in the [Rendering] section</li>
        <li>Environment: <code>export SPIDY_RENDERING_USE_SOFTWARE_RENDERING=True</code></li>
        <li>Command line: <code>python main.py --rendering.use_software_rendering=True</code></li>
    </ul>
    """
    
    config_label = QLabel(config_text)
    config_label.setWordWrap(True)
    
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.addWidget(config_label)
    scroll_area.setWidget(scroll_content)
    
    layout.addWidget(scroll_area)

    # Add buttons
    buttons_layout = QHBoxLayout()
    
    open_config_button = QPushButton("Open Config File")
    open_config_button.clicked.connect(self.open_config_file)
    buttons_layout.addWidget(open_config_button)
    
    reload_config_button = QPushButton("Reload Config")
    reload_config_button.clicked.connect(self.reload_config)
    buttons_layout.addWidget(reload_config_button)
    
    save_config_button = QPushButton("Save Config")
    save_config_button.clicked.connect(self.save_config)
    buttons_layout.addWidget(save_config_button)
    
    layout.addLayout(buttons_layout)
    
    # Add close button
    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    button_box.rejected.connect(config_dialog.reject)
    layout.addWidget(button_box)

    config_dialog.setLayout(layout)
    config_dialog.exec()

def open_config_file(self):
    """Open the configuration file in the default text editor"""
    config_path = os.path.join(self.config_dir, "config.ini")
    if os.path.exists(config_path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(config_path))
    else:
        QMessageBox.warning(self, "Config File Not Found", 
                           f"Configuration file not found at: {config_path}")

def reload_config(self):
    """Reload the configuration from disk"""
    self.config.load_config()
    self._configure_browser_settings()
    QMessageBox.information(self, "Configuration Reloaded", 
                           "The configuration has been reloaded. Some changes may require a restart.")

def save_config(self):
    """Save the current configuration to disk"""
    self.config.save_config()
    QMessageBox.information(self, "Configuration Saved", 
                           "The configuration has been saved to ~/.spidy/config.ini")
