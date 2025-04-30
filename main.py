"""
Spidy Web Browser - Main Entry Point

Initializes the Qt application and creates the browser instance.
Handles the critical initialization sequence required for Qt and QtWebEngine.
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngine import QtWebEngine
from PyQt5 import QtCore

from browser import Browser

def main():
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Configure Qt core attributes before initializing QApplication
    QtCore.QCoreApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)

    # Initialize QtWebEngine before creating QApplication
    QtWebEngine.initialize()

    # Create application instance
    app = QApplication(sys.argv)

    # Create and show browser
    browser = Browser()
    browser.show()

    # Save history and bookmarks on application exit
    app.aboutToQuit.connect(browser.navigation_manager.save_history)
    app.aboutToQuit.connect(browser.bookmark_manager.save_bookmarks)

    # Start event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

