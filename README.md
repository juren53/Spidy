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

## Project Structure

```
.
├── main.py              # Application entry point
├── browser.py           # Main browser class
├── link_handler.py      # URL navigation and security handler
├── navigation_manager.py # Navigation and history management
├── tab_manager.py       # Tab operations handler
├── bookmark_manager.py  # Bookmark management
├── ui_manager.py        # UI components handler
└── README.md            # Project documentation
```

## Requirements

- Python 3.x
- PyQt5
- PyQtWebEngine

## Installation

1. Install required packages:
```bash
pip install PyQt5 PyQtWebEngine
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/spidy.git
cd spidy
```

3. Run the browser:
```bash
python main.py
```

## Configuration

- Configuration files are stored in `~/.spidy/`
- Bookmarks are saved in `~/.spidy/bookmarks.json`
- History is saved in `~/.spidy/history.json`

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

