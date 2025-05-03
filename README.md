# Spidy Web Browser

A standards-based, open-source web browser built with Python and PyQt5. Provides basic browsing functionality, bookmarks, history tracking, and statistics.

## Features

- Multiple tab support with tab management
- Bookmark management
- Browsing history tracking
- Page statistics
- Security-focused URL handling
- File operations (open/save pages)
- Keyboard shortcuts
- Markdown file rendering and navigation

## Project Structure

```
.
├── main.py                # Application entry point
├── browser.py             # Main browser class
├── link_handler.py        # URL navigation and security handler
├── navigation_manager.py  # Navigation and history management
├── tab_manager.py         # Tab operations handler
├── bookmark_manager.py    # Bookmark management
├── ui_manager.py          # UI components handler
├── statistics_manager.py  # Usage statistics tracking
├── README.md              # Project overview
├── assets/                # Image assets and icons
├── tests/                 # Test files and test utilities
├── info/                  # Documentation and project information
└── archive/               # Archived code samples and experiments
```

## Requirements

- Python 3.x
- PyQt5
- PyQtWebEngine
- Markdown

## Installation

1. Install required packages:
```bash
pip install PyQt5 PyQtWebEngine
pip install markdown
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/spidy.git
cd Spidy
```

3. Run the browser:
```bash
python main.py
```

## Configuration

- Configuration files are stored in `~/.spidy/`
- Bookmarks are saved in `~/.spidy/bookmarks.json`
- History is saved in `~/.spidy/history.json`
- Project documentation is available in the `info/` directory

## Keyboard Shortcuts

- Ctrl+T: New tab
- Ctrl+W: Close current tab
- Ctrl+Tab: Next tab
- Ctrl+Shift+Tab: Previous tab
- Left Arrow: Back (when history available)
- Right Arrow: Forward (when history available)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

