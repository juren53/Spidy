#!/bin/bash

# Spidy Browser Runner
# This script demonstrates how to run Spidy browser with different configuration options

# Function to show usage
show_usage() {
    echo "Spidy Browser Runner"
    echo "Usage: ./run_spidy.sh [options]"
    echo ""
    echo "Options:"
    echo "  --help                  Show this help message"
    echo "  --software-rendering    Run with software rendering (default)"
    echo "  --hardware-rendering    Run with hardware rendering"
    echo "  --home=URL              Set homepage URL"
    echo "  --no-js                 Disable JavaScript"
    echo "  --webgl                 Enable WebGL"
    echo "  --user-agent=STRING     Set custom user agent"
    echo "  --reset-config          Reset to default configuration"
    echo ""
    echo "Examples:"
    echo "  ./run_spidy.sh --software-rendering --home=https://duckduckgo.com"
    echo "  ./run_spidy.sh --hardware-rendering --webgl"
    echo "  SPIDY_RENDERING_USE_SOFTWARE_RENDERING=True python main.py"
    echo ""
}

# Default settings
SOFTWARE_RENDERING=true
HOME_PAGE=""
ENABLE_JS=true
ENABLE_WEBGL=false
USER_AGENT=""
RESET_CONFIG=false

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --help)
            show_usage
            exit 0
            ;;
        --software-rendering)
            SOFTWARE_RENDERING=true
            shift
            ;;
        --hardware-rendering)
            SOFTWARE_RENDERING=false
            shift
            ;;
        --home=*)
            HOME_PAGE="${arg#*=}"
            shift
            ;;
        --no-js)
            ENABLE_JS=false
            shift
            ;;
        --webgl)
            ENABLE_WEBGL=true
            shift
            ;;
        --user-agent=*)
            USER_AGENT="${arg#*=}"
            shift
            ;;
        --reset-config)
            RESET_CONFIG=true
            shift
            ;;
        *)
            echo "Unknown option: $arg"
            show_usage
            exit 1
            ;;
    esac
done

# Reset configuration if requested
if [ "$RESET_CONFIG" = true ]; then
    echo "Resetting configuration..."
    rm -f ~/.spidy/config.ini
fi

# Set environment variables based on settings
if [ "$SOFTWARE_RENDERING" = true ]; then
    export SPIDY_RENDERING_USE_SOFTWARE_RENDERING=True
    # Also set the Qt environment variables directly for immediate effect
    export QT_OPENGL=software
    export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu"
    export LIBGL_ALWAYS_SOFTWARE=1
    
    echo "Enabled software rendering"
else
    export SPIDY_RENDERING_USE_SOFTWARE_RENDERING=False
    echo "Using hardware rendering"
fi

if [ -n "$HOME_PAGE" ]; then
    export SPIDY_GENERAL_HOME_PAGE="$HOME_PAGE"
    echo "Set home page to: $HOME_PAGE"
fi

if [ "$ENABLE_JS" = false ]; then
    export SPIDY_BROWSER_JAVASCRIPT_ENABLED=False
    echo "Disabled JavaScript"
fi

if [ "$ENABLE_WEBGL" = true ]; then
    export SPIDY_RENDERING_WEBGL_ENABLED=True
    echo "Enabled WebGL"
fi

if [ -n "$USER_AGENT" ]; then
    export SPIDY_BROWSER_USER_AGENT="$USER_AGENT"
    echo "Set custom user agent"
fi

# Run the browser
echo "Starting Spidy browser..."
python main.py

exit 0
