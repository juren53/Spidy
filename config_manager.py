"""
Spidy Web Browser - Configuration Manager

Handles loading and saving configuration settings from multiple sources:
1. Default settings (hardcoded)
2. Configuration file (~/.spidy/config.ini)
3. Environment variables (with prefix SPIDY_)
4. Command line arguments (highest priority)

Configuration values can be retrieved with a simple API and are cached for performance.
"""

import os
import sys
import configparser
from typing import Any, Dict, Optional, List, Set

class ConfigManager:
    """Manages application configuration with multiple source support"""
    
    # Configuration key prefixes
    ENV_PREFIX = "SPIDY_"
    
    # Configuration sections
    SECTION_GENERAL = "General"
    SECTION_BROWSER = "Browser"
    SECTION_RENDERING = "Rendering"
    SECTION_NETWORK = "Network"
    SECTION_PRIVACY = "Privacy"
    
    # Default configuration values
    DEFAULT_CONFIG = {
        SECTION_GENERAL: {
            "home_page": "https://search.brave.com/",
            "show_bookmarks_bar": "True",
            "cache_dir": "",  # Empty means use default (~/.spidy/cache)
        },
        SECTION_BROWSER: {
            "user_agent": "",  # Empty means use default Qt WebEngine user agent
            "javascript_enabled": "True",
            "save_history": "True",
        },
        SECTION_RENDERING: {
            "use_software_rendering": "True",
            "webgl_enabled": "False",
            "default_zoom": "100",
        },
        SECTION_NETWORK: {
            "proxy_enabled": "False",
            "proxy_host": "",
            "proxy_port": "",
            "proxy_type": "http",  # http, socks5
        },
        SECTION_PRIVACY: {
            "do_not_track": "True",
            "block_third_party_cookies": "True",
        }
    }
    
    def __init__(self, config_dir: str = None):
        """Initialize the configuration manager"""
        # Set configuration directory (default to ~/.spidy)
        if config_dir is None:
            self.config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        else:
            self.config_dir = config_dir
            
        # Ensure config directory exists
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Set paths
        self.config_path = os.path.join(self.config_dir, 'config.ini')
        
        # Initialize configuration parser
        self.config = configparser.ConfigParser()
        
        # Initialize with default values
        for section, options in self.DEFAULT_CONFIG.items():
            self.config[section] = {}
            for option, value in options.items():
                self.config[section][option] = value
        
        # Load configuration from file if it exists
        self.load_config()
        
        # Apply environment variables on top of loaded configuration
        self.apply_environment_variables()
        
        # Apply command line arguments (highest priority)
        self.apply_command_line_arguments()
        
    def load_config(self) -> None:
        """Load configuration from config.ini file"""
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path)
                print(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                print(f"Error loading configuration: {e}")
                
    def save_config(self) -> None:
        """Save current configuration to config.ini file"""
        try:
            with open(self.config_path, 'w') as config_file:
                self.config.write(config_file)
            print(f"Saved configuration to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def apply_environment_variables(self) -> None:
        """Apply relevant environment variables to configuration"""
        for env_var, value in os.environ.items():
            if env_var.startswith(self.ENV_PREFIX):
                # Extract the relevant part (e.g., SPIDY_RENDERING_USE_SOFTWARE_RENDERING -> RENDERING_USE_SOFTWARE_RENDERING)
                config_key = env_var[len(self.ENV_PREFIX):]
                
                # Split by underscore to get section and option
                parts = config_key.split('_', 1)
                if len(parts) == 2:
                    section, option = parts
                    section = section.title()  # Convert to title case to match section names
                    option = option.lower()    # Convert to lowercase for option names
                    
                    # Use the section if it exists in our config
                    if section in self.config:
                        # Convert environment variable key format to config format
                        # Example: USE_SOFTWARE_RENDERING -> use_software_rendering
                        formatted_option = '_'.join(p.lower() for p in option.split('_'))
                        
                        # Set the configuration value if the option exists
                        for existing_option in self.config[section]:
                            if existing_option.replace('_', '') == formatted_option.replace('_', ''):
                                self.config[section][existing_option] = value
                                print(f"Applied environment variable {env_var}={value}")
                                break
    
    def apply_command_line_arguments(self) -> None:
        """Apply command line arguments to configuration"""
        # Example parsing of --setting=value format
        for arg in sys.argv[1:]:
            if arg.startswith('--') and '=' in arg:
                setting, value = arg[2:].split('=', 1)
                
                # Split setting into section and option (e.g., rendering.use_software_rendering)
                if '.' in setting:
                    section, option = setting.split('.', 1)
                    section = section.title()  # Convert to title case to match section names
                    
                    # Set the configuration value if the section and option exist
                    if section in self.config and option in self.config[section]:
                        self.config[section][option] = value
                        print(f"Applied command line argument --{setting}={value}")
    
    def get(self, section: str, option: str, fallback: Any = None) -> Any:
        """Get a configuration value with fallback"""
        try:
            return self.config[section][option]
        except (KeyError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_boolean(self, section: str, option: str, fallback: bool = False) -> bool:
        """Get a boolean configuration value"""
        try:
            return self.config.getboolean(section, option)
        except (ValueError, KeyError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_int(self, section: str, option: str, fallback: int = 0) -> int:
        """Get an integer configuration value"""
        try:
            return self.config.getint(section, option)
        except (ValueError, KeyError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_float(self, section: str, option: str, fallback: float = 0.0) -> float:
        """Get a float configuration value"""
        try:
            return self.config.getfloat(section, option)
        except (ValueError, KeyError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def set(self, section: str, option: str, value: Any) -> None:
        """Set a configuration value"""
        # Ensure section exists
        if section not in self.config:
            self.config[section] = {}
        
        # Set the value
        self.config[section][option] = str(value)
    
    def create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist"""
        if not os.path.exists(self.config_path):
            self.save_config()
            print(f"Created default configuration file at {self.config_path}")
            
    def get_environment_vars(self) -> Dict[str, str]:
        """
        Get a dictionary of all environment variables that would affect Spidy
        
        Returns:
            Dictionary of environment variable name to value
        """
        env_vars = {}
        for env_var, value in os.environ.items():
            if env_var.startswith(self.ENV_PREFIX):
                env_vars[env_var] = value
        return env_vars
    
    def get_render_environment_vars(self) -> Dict[str, str]:
        """
        Get necessary environment variables for rendering based on config
        
        Returns:
            Dictionary of environment variable name to value
        """
        env_vars = {}
        
        # Check if software rendering is enabled
        if self.get_boolean(self.SECTION_RENDERING, "use_software_rendering", True):
            env_vars["QT_OPENGL"] = "software"
            env_vars["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
            env_vars["LIBGL_ALWAYS_SOFTWARE"] = "1"
            
        # Add other rendering-related environment variables as needed
        
        return env_vars
    
    def apply_render_environment_vars(self) -> None:
        """Apply rendering environment variables to the current process"""
        render_env_vars = self.get_render_environment_vars()
        for key, value in render_env_vars.items():
            os.environ[key] = value
            
    def __str__(self) -> str:
        """String representation of the configuration"""
        result = []
        for section in self.config.sections():
            result.append(f"[{section}]")
            for option in self.config[section]:
                result.append(f"{option} = {self.config[section][option]}")
            result.append("")
        return "\n".join(result)

# Global instance
_config_manager = None

def get_config() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
