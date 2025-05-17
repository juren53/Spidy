"""
Spidy Web Browser - Main Entry Point

Initializes the Qt application and creates the browser instance.
Handles the critical initialization sequence required for Qt and QtWebEngine.
"""

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore

from browser import Browser

def main():
    # High DPI scaling is enabled by default in Qt6
    # Configure Qt core attributes before initializing QApplication
    QtCore.QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    QtCore.QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi, True)  # Replacement for AA_DisableHighDpiScaling
    QtCore.QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    QtCore.QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)

    # WebEngine initialization is automatic in PyQt6
    # No need for explicit initialization

    # Create application instance
    app = QApplication(sys.argv)

    # Create and show browser
    browser = Browser()
    browser.show()

    # Save history and bookmarks on application exit
    app.aboutToQuit.connect(browser.navigation_manager.save_history)
    app.aboutToQuit.connect(browser.bookmark_manager.save_bookmarks)

    # Start event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

