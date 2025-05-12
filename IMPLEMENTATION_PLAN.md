# Spidy Browser Configuration Implementation Plan

This document outlines the steps to implement a comprehensive configuration system for the Spidy Browser, allowing settings to be controlled through config files, environment variables, and command-line arguments.

## Overview

The new configuration system will:

1. Support hierarchical configuration with multiple sources:
   - Default hardcoded values (lowest priority)
   - Config file settings (`~/.spidy/config.ini`)
   - Environment variables with `SPIDY_` prefix
   - Command-line arguments (highest priority)

2. Automatically handle environment variables that control rendering options
   - Support software rendering via environment variables
   - No need to manually set QT_OPENGL, etc. when launching

3. Provide user interface for viewing and editing configuration

## Files to Create/Modify

### 1. Create `config_manager.py`

This new file implements the `ConfigManager` class that handles all configuration operations:
- Loading/saving from config.ini file
- Reading environment variables
- Parsing command-line arguments
- Providing API to get/set values with proper type conversion

### 2. Create default `config.ini` template

Add a default configuration file at `~/.spidy/config.ini` that includes settings for:
- General browser settings (home page, bookmarks bar)
- Rendering options (software rendering, WebGL)
- Network settings (proxy)
- Privacy options (cookies, Do Not Track)

### 3. Modify `main.py`

Update to initialize the configuration system before any Qt imports:
- Import and initialize ConfigManager first
- Apply environment variables before QApplication is created
- Use configuration values for startup options

### 4. Update `browser.py`

Add configuration-related functionality:
- Use ConfigManager for browser settings
- Add configuration UI dialog
- Apply rendering settings from config
- Add configuration reload functionality

### 5. Create `run_spidy.sh` helper script

A helper script that demonstrates how to:
- Use environment variables to control configuration
- Provide command-line options for common settings
- Show examples of different configuration approaches

## Implementation Steps

1. **Setup Configuration Infrastructure**
   - Create ConfigManager class
   - Implement configuration file loading/saving
   - Add environment variable handling
   - Add command-line argument parsing

2. **Integrate with Main Application**
   - Modify main.py to use ConfigManager early in startup
   - Update Browser class to use configuration values
   - Ensure rendering settings are applied correctly

3. **Add Configuration UI**
   - Create configuration dialog in Browser class
   - Add ability to view current settings
   - Provide interface to edit and save settings
   - Add help text explaining configuration options

4. **Testing**
   - Test with various environment variables
   - Verify software rendering works correctly
   - Ensure configuration file is saved/loaded properly
   - Validate command-line argument handling

## File Integration Instructions

### Integrating `config_manager.py`

Copy the entire file into your project directory. This is a new file that doesn't replace any existing code.

### Updating `main.py`

Replace your existing `main.py` with the new version or manually make these changes:

1. Add import at the top of the file:
   ```python
   from config_manager import get_config
   ```

2. Modify the `main()` function to initialize and use configuration:
   ```python
   def main():
       # Initialize the configuration manager
       config = get_config()
       
       # Create default config file if it doesn't exist
       config.create_default_config()
       
       # Apply rendering environment variables from configuration
       config.apply_render_environment_vars()
       
       # Then continue with the rest of the function...
   ```

3. Update the Qt attribute setting to use configuration values:
   ```python
   # Only set software OpenGL if configured
   if config.get_boolean("Rendering", "use_software_rendering", True):
       QtCore.QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)
   ```

### Updating `browser.py`

These changes are more extensive. Either:

1. Use the provided patch file as a reference to manually update your browser.py
2. Or, modify these specific sections:

   - Add import for ConfigManager:
     ```python
     from config_manager import get_config
     ```
   
   - Update `__init__` method to use config
   - Add the new `_configure_browser_settings` method
   - Update `closeEvent` to save config
   - Add the new configuration UI methods (show_config, etc.)

## Usage Examples

### Environment Variables

```bash
# Run with software rendering
SPIDY_RENDERING_USE_SOFTWARE_RENDERING=True python main.py

# Change home page
SPIDY_GENERAL_HOME_PAGE=https://duckduckgo.com python main.py

# Disable JavaScript
SPIDY_BROWSER_JAVASCRIPT_ENABLED=False python main.py

# Combined options
SPIDY_RENDERING_USE_SOFTWARE_RENDERING=True SPIDY_GENERAL_HOME_PAGE=https://example.com python main.py
```

### Command Line Arguments

```bash
# Run with software rendering disabled
python main.py --rendering.use_software_rendering=False

# Change home page
python main.py --general.home_page=https://duckduckgo.com

# Multiple options
python main.py --rendering.use_software_rendering=True --browser.javascript_enabled=False
```

### Configuration File

Edit `~/.spidy/config.ini`:

```ini
[General]
home_page = https://example.com
show_bookmarks_bar = True

[Rendering]
use_software_rendering = True
webgl_enabled = False
```

## Final Notes

1. The configuration system prioritizes settings in this order (highest to lowest):
   - Command-line arguments
   - Environment variables
   - Config file settings
   - Default hardcoded values

2. Some settings may require restarting the application to take effect

3. The configuration UI will show the currently active settings from all sources

4. The `~/.spidy/config.ini` file will be created automatically if it doesn't exist
