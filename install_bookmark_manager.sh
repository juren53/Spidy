#!/bin/bash

# Spidy Bookmark Manager Installer
# This script installs the Spidy Bookmark Manager to the user's system

# Set up variables
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create installation directories if they don't exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"

# Copy the bookmark manager script
echo "Installing bookmark manager script..."
cp "$SCRIPT_DIR/spidy_bookmark_manager.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/spidy_bookmark_manager.py"

# Update the desktop file with the correct path
sed "s|Exec=.*|Exec=$INSTALL_DIR/spidy_bookmark_manager.py|g" "$SCRIPT_DIR/spidy-bookmark-manager.desktop" > "$DESKTOP_DIR/spidy-bookmark-manager.desktop"

# Ensure the desktop file is executable
chmod +x "$DESKTOP_DIR/spidy-bookmark-manager.desktop"

echo "Installation complete!"
echo "You can now run the Spidy Bookmark Manager from your applications menu"
echo "or by running 'spidy_bookmark_manager.py' from the terminal."

# Check if PyQt6 is installed
if ! python -c "import PyQt6" &> /dev/null; then
    echo ""
    echo "WARNING: PyQt6 does not appear to be installed."
    echo "You will need to install it before running the bookmark manager:"
    echo "pip install PyQt6"
fi

exit 0
