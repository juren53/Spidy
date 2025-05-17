 ### --- UPDATED: tab_manager.py ---
import os
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWidgets import QTabWidget, QPushButton
from link_handler import LinkHandler
from web_view import WebEngineView

class TabManager:
    def __init__(self, browser):
        self.browser = browser
        self.tabs = []
        self.setup_tab_widget()

    def setup_tab_widget(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(QSize(24, 24))
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)

    def current_view(self):
        return self.tab_widget.currentWidget()

    def add_new_tab(self, qurl=None):
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

        browser = WebEngineView(self.browser)
        page = LinkHandler(browser)
        browser.setPage(page)

        self._configure_tab(browser)
        self.tabs.append(browser)
        tab_index = self.tab_widget.addTab(browser, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)
        browser.setUrl(qurl)
        self.browser.navigation_manager.update_url_field(qurl)

        return browser

    def add_new_tab_page(self):
        browser = WebEngineView(self.browser)
        page = LinkHandler(browser)
        browser.setPage(page)

        self._configure_tab(browser)
        self.tabs.append(browser)
        tab_index = self.tab_widget.addTab(browser, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)

        return page

    def _configure_tab(self, browser):
        page = browser.page()
        if isinstance(page, LinkHandler):
            page.open_url_in_new_tab.connect(self.open_url_in_new_tab)
            page.link_clicked_new_tab.connect(self.open_link_in_new_tab)

        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)

        browser.urlChanged.connect(lambda url, b=browser: self.browser.navigation_manager.update_url_field(url))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(b))
        browser.loadFinished.connect(lambda ok: self.browser.navigation_manager.add_to_history(ok, browser))
        browser.titleChanged.connect(lambda title, b=browser: self.browser.navigation_manager.update_history_title(title, b))
        browser.loadFinished.connect(lambda: self.browser.navigation_manager.update_navigation_buttons())
        browser.urlChanged.connect(lambda: self.browser.navigation_manager.update_navigation_buttons())

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
            browser = self.tabs.pop(index)
            browser.deleteLater()

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())

    def open_url_in_new_tab(self, url):
        self.add_new_tab(url)

    def open_link_in_new_tab(self, href, target):
        url = QUrl(href)
        if not url.isValid():
            url = QUrl("http://" + href) if not href.startswith("http") else QUrl(href)
        self.add_new_tab(url)

    def tab_changed(self, index):
        if index >= 0 and self.tabs:
            qurl = self.tabs[index].url()
            self.browser.navigation_manager.update_url_field(qurl)
            self.browser.navigation_manager.update_navigation_buttons()

    def next_tab(self):
        current = self.tab_widget.currentIndex()
        self.tab_widget.setCurrentIndex((current + 1) % self.tab_widget.count())

    def previous_tab(self):
        current = self.tab_widget.currentIndex()
        self.tab_widget.setCurrentIndex(current - 1 if current > 0 else self.tab_widget.count() - 1)

    def update_tab_title(self, browser):
        index = self.tab_widget.indexOf(browser)
        if index != -1:
            title = browser.page().title()
            self.tab_widget.setTabText(index, title[:20] + '...' if len(title) > 20 else title)

