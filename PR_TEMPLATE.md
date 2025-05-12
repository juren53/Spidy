# Add Configuration System with Environment Variable Support

## Overview
This PR adds a comprehensive configuration system to Spidy Browser that allows settings to be controlled through configuration files, environment variables, and command-line arguments. It specifically addresses the need to include system environment variables in the Python code and provides a standardized approach for configuration management.

## Changes
- Added new `config_manager.py` file to handle configuration from multiple sources
- Created default configuration template in `~/.spidy/config.ini`
- Updated `main.py` to initialize configuration before Qt imports
- Modified `browser.py` to use configuration values and added configuration UI
- Added helper script `run_spidy.sh` for launching with different configurations
- Created implementation plan and documentation

## Features
- **Hierarchical Configuration**: Settings can be specified through:
  1. Default hardcoded values
  2. Configuration file (`~/.spidy/config.ini`)
  3. Environment variables with `SPIDY_` prefix
  4. Command-line arguments

- **Environment Variable Support**: 
  - Direct mapping of environment variables to configuration options
  - Automatic application of rendering-related variables (QT_OPENGL, etc.)
  - Naming convention: `SPIDY_SECTION_OPTION=value`

- **Configuration UI**:
  - New dialog to view current configuration
  - Shows active environment variables
  - Button to open config file in text editor
  - Options to reload and save configuration

- **Software Rendering Control**:
  - Simplified control of rendering options
  - No need to manually set multiple environment variables

## Implementation Details
- ConfigManager uses Python's configparser for .ini file handling
- Environment variables are automatically mapped to configuration sections/options
- Rendering-related environment variables are applied before QApplication creation
- Software rendering is enabled by default but can be disabled via configuration

## Testing
- Tested with various environment variable combinations
- Verified software rendering works correctly
- Confirmed configuration file is saved and loaded properly
- Validated command-line argument handling

## Screenshots
[Add screenshots of the configuration UI here]

## How to Use

### Environment Variables
```bash
# Run with software rendering
SPIDY_RENDERING_USE_SOFTWARE_RENDERING=True python main.py

# Change home page
SPIDY_GENERAL_HOME_PAGE=https://duckduckgo.com python main.py

# Disable JavaScript
SPIDY_BROWSER_JAVASCRIPT_ENABLED=False python main.py
```

### Command-Line Arguments
```bash
python main.py --rendering.use_software_rendering=False
python main.py --general.home_page=https://example.com
```

### Configuration File
Edit `~/.spidy/config.ini`:
```ini
[Rendering]
use_software_rendering = True
webgl_enabled = False

[General]
home_page = https://example.com
```
