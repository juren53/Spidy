"""
Tab Manager for Spidy Web Browser

Handles tab creation, deletion, and management.
"""

import os
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWidgets import QTabWidget, QPushButton
from link_handler import LinkHandler
from web_view import WebEngineView

class TabManager:
    def __init__(self, browser):
        self.browser = browser
        self.tabs = []
        self.setup_tab_widget()

    def setup_tab_widget(self):
        """Initialize the tab widget and its settings"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Add tab button
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(QSize(24, 24))
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

    def current_view(self):
        """Get the current active WebView"""
        return self.tab_widget.currentWidget()

    def add_new_tab(self, qurl=None):
        """Add a new browser tab"""
        if qurl is None or isinstance(qurl, bool):
            qurl = QUrl('https://search.brave.com/')
        elif isinstance(qurl, str):
            if not qurl.startswith(('http://', 'https://', 'file://')):
                if os.path.exists(qurl):
                    qurl = QUrl.fromLocalFile(os.path.abspath(qurl))
                else:
                    qurl = QUrl('http://' + qurl)
            else:
                qurl = QUrl(qurl)

        # Create browser view with custom page handler and zoom support
        browser = WebEngineView()
        page = LinkHandler(browser)
        browser.setPage(page)
        
        # Configure tab settings and connections
        self._configure_tab(browser)
        
        # Add to tabs list and widget
        self.tabs.append(browser)
        tab_index = self.tab_widget.addTab(browser, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Set URL and update field
        browser.setUrl(qurl)
        self.browser.navigation_manager.update_url_field(qurl)
        
        return browser

    def _configure_tab(self, browser):
        """Configure settings and connections for a new tab"""
        # Configure settings
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)

        # Configure signal connections
        browser.urlChanged.connect(
            lambda url, b=browser: self.browser.navigation_manager.update_url_field(url))
        browser.titleChanged.connect(
            lambda title, b=browser: self.update_tab_title(b))
        browser.loadFinished.connect(
            lambda ok: self.browser.navigation_manager.add_to_history(ok, browser))
        browser.titleChanged.connect(
            lambda title, b=browser: self.browser.navigation_manager.update_history_title(title, b))
        browser.loadFinished.connect(
            lambda: self.browser.navigation_manager.update_navigation_buttons())
        browser.urlChanged.connect(
            lambda: self.browser.navigation_manager.update_navigation_buttons())

    def close_tab(self, index):
        """Close the tab at the given index"""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
            browser = self.tabs.pop(index)
            browser.deleteLater()

    def close_current_tab(self):
        """Close the currently active tab"""
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)

    def tab_changed(self, index):
        """Handle tab change events"""
        if index >= 0 and self.tabs:
            qurl = self.tabs[index].url()
            self.browser.navigation_manager.update_url_field(qurl)
            self.browser.navigation_manager.update_navigation_buttons()

    def next_tab(self):
        """Switch to the next tab"""
        current = self.tab_widget.currentIndex()
        if current < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current + 1)
        else:
            self.tab_widget.setCurrentIndex(0)

    def previous_tab(self):
        """Switch to the previous tab"""
        current = self.tab_widget.currentIndex()
        if current > 0:
            self.tab_widget.setCurrentIndex(current - 1)
        else:
            self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def update_tab_title(self, browser):
        """Update tab title when page title changes"""
        index = self.tab_widget.indexOf(browser)
        if index != -1:
            title = browser.page().title()
            if title:
                self.tab_widget.setTabText(index, title[:20] + '...' if len(title) > 20 else title)
            else:
                self.tab_widget.setTabText(index, 'New Tab')

