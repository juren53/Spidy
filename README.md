# Spidy Web Browser

A standards-based, open-source web browser built with Python and PyQt6.

## Features

- Multiple tab support
- Bookmark management
- Browsing history
- Markdown file rendering
- Page zoom functionality
- Security-focused navigation

## Requirements

- Python 3.8+
- PyQt6
- PyQt6-WebEngine

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Spidy.git
   cd Spidy
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the Browser

### Standard Execution

```bash
python main.py
```

### With Software Rendering (for environments with GPU/graphics issues)

If you encounter graphics-related errors like "Failed to create GBM buffer for GLX" or "Failed to get fd for plane", use software rendering:

```bash
QT_OPENGL=software QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu" LIBGL_ALWAYS_SOFTWARE=1 python main.py
```

### Creating an Alias for Easy Use

Add this line to your ~/.bashrc file for convenience:

```bash
echo 'alias spidy="QT_OPENGL=software QTWEBENGINE_CHROMIUM_FLAGS=\"--disable-gpu\" LIBGL_ALWAYS_SOFTWARE=1 python /path/to/Spidy/main.py\""' >> ~/.bashrc
```

Then reload your .bashrc file:

```bash
source ~/.bashrc
```

Now you can simply type `spidy` to launch the browser with software rendering.

## Common Issues

### Graphics Rendering Problems

If you encounter errors related to GPU or graphics rendering:
- The application uses software rendering by default via `AA_UseSoftwareOpenGL`
- For environments with problematic graphics drivers (especially Nouveau), use the software rendering command above
- More details can be found in the Qt5-Core-Dump-Analysis.txt file

## License

MIT
