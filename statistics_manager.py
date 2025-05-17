"""
Statistics Manager for Spidy Web Browser

Handles collection and display of webpage statistics.
"""

from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QGridLayout

class StatisticsManager:
    def __init__(self, browser):
        self.browser = browser

    def view_statistics(self):
        """Show statistics about the current webpage"""
        current_view = self.browser.tab_manager.current_view()
        if not current_view:
            return

        def on_stats_ready(stats):
            dialog = self.create_statistics_dialog(stats)
            dialog.exec()

        self.collect_page_statistics(on_stats_ready)

    def collect_page_statistics(self, callback):
        """Collect statistics about the current webpage using JavaScript"""
        current_view = self.browser.tab_manager.current_view()
        if not current_view:
            callback({
                'title': 'No page loaded',
                'url': '',
                'domain': '',
                'protocol': '',
                'pageSize': 0,
                'numLinks': 0,
                'numImages': 0,
                'numScripts': 0,
                'numStylesheets': 0,
                'metaTags': 0
            })
            return

        # JavaScript to collect page statistics
        js_code = """
        (function() {
            return {
                title: document.title || '',
                url: window.location.href || '',
                domain: window.location.hostname || '',
                protocol: window.location.protocol || '',
                pageSize: document.documentElement.outerHTML.length,
                numLinks: document.getElementsByTagName('a').length,
                numImages: document.getElementsByTagName('img').length,
                numScripts: document.getElementsByTagName('script').length,
                numStylesheets: document.getElementsByTagName('link').length,
                metaTags: document.getElementsByTagName('meta').length
            };
        })();
        """

        current_view.page().runJavaScript(js_code, callback)

    def create_statistics_dialog(self, stats):
        """Create a dialog displaying the webpage statistics"""
        dialog = QDialog(self.browser)
        dialog.setWindowTitle("Page Statistics")
        dialog.resize(400, 300)

        layout = QGridLayout()
        row = 0

        # Add statistics to grid layout
        stats_items = [
            ("Title", stats.get('title', 'N/A')),
            ("URL", stats.get('url', 'N/A')),
            ("Domain", stats.get('domain', 'N/A')),
            ("Protocol", stats.get('protocol', 'N/A')),
            ("Page Size", f"{stats.get('pageSize', 0)} bytes"),
            ("Links", stats.get('numLinks', 0)),
            ("Images", stats.get('numImages', 0)),
            ("Scripts", stats.get('numScripts', 0)),
            ("Stylesheets", stats.get('numStylesheets', 0)),
            ("Meta Tags", stats.get('metaTags', 0)),
            ("Current Time", QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss'))
        ]

        for label, value in stats_items:
            layout.addWidget(QLabel(f"<b>{label}:</b>"), row, 0)
            layout.addWidget(QLabel(str(value)), row, 1)
            row += 1

        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box, row, 0, 1, 2)

        dialog.setLayout(layout)
        return dialog

