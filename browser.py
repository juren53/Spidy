"""
Spidy Web Browser - Main Browser Class

A standards-based, open-source web browser built with Python and PyQt6.
Provides basic browsing functionality, bookmarks, history tracking, and statistics.
"""

import os
import subprocess
import sys
from datetime import datetime
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import Qt, QUrl, QDateTime
from PyQt6.QtWidgets import QMainWindow, QWidget, QFileDialog, QMessageBox, QApplication
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QPushButton, QScrollArea
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QToolBar, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile, QWebEngineScript

# Import the config manager if available
try:
    from config_manager import get_config
except ImportError:
    get_config = None

from navigation_manager import NavigationManager
from tab_manager import TabManager
from bookmark_manager import BookmarkManager
from ui_manager import UIManager
from statistics_manager import StatisticsManager

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize configuration directory
        self.config_dir = os.path.join(os.path.expanduser('~'), '.spidy')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize manager classes
        self.tab_manager = TabManager(self)
        self.navigation_manager = NavigationManager(self)
        self.bookmark_manager = BookmarkManager(self)
        self.statistics_manager = StatisticsManager(self)
        self.ui_manager = UIManager(self)

        # Create initial tab with configured home page or default
        home_url = self.get_home_page_url()
        self.tab_manager.add_new_tab(home_url)
        
        self.show()


    def get_home_page_url(self):
        """Get the configured home page URL or the default"""
        default_home_page = "https://search.brave.com/"
        
        # Try to get home page from configuration if available
        if get_config:
            config = get_config()
            home_page = config.get("General", "home_page", default_home_page)
            return QUrl(home_page)
        
        # Fallback to default if config not available
        return QUrl(default_home_page)


    def keyPressEvent(self, event):
        """Handle keyboard navigation events"""
        current_view = self.tab_manager.current_view()
        if not current_view:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Left and current_view.page().history().canGoBack():
            self.navigation_manager.view_back()
        elif event.key() == Qt.Key.Key_Right and current_view.page().history().canGoForward():
            self.navigation_manager.view_forward()
        else:
            super().keyPressEvent(event)

    def open_file(self):
        """Open a local HTML or MD file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            os.path.expanduser("~"),
            "Web Files (*.html *.htm *.md);;HTML Files (*.html *.htm);;Markdown Files (*.md);;All Files (*)"
        )
        
        if filepath:
            url = QUrl.fromLocalFile(os.path.abspath(filepath))
            self.tab_manager.add_new_tab(url)

    def save_page(self):
        """Save the current webpage to a file"""
        current_view = self.tab_manager.current_view()
        if not current_view:
            return
            
        current_url = current_view.url()
        suggested_filename = current_url.fileName() or "webpage.html"
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Page", 
            os.path.join(os.path.expanduser("~"), suggested_filename),
            "HTML Files (*.html *.htm);;All Files (*)"
        )
        
        if filepath:
            if not filepath.lower().endswith(('.html', '.htm')):
                filepath += '.html'
                
            # Simply call save with the filepath
            current_view.page().save(filepath)
            QMessageBox.information(self, "Save Complete", 
                                  "The page has been saved successfully.")

    def closeEvent(self, event):
        """Handle application close event"""
        self.navigation_manager.save_history()
        self.bookmark_manager.save_bookmarks()
        super().closeEvent(event)

    def view_statistics(self):
        """Show statistics about the current webpage"""
        self.statistics_manager.view_statistics()

    def show_help(self):
        """Show help dialog"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Spidy Help")
        help_dialog.resize(500, 450)  # Slightly increase height for new content

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>Spidy Browser Help</h2>"))
        layout.addWidget(QLabel("""
            <p>Welcome to Spidy, an open-source web browser built with Python and PyQt6!</p>
            <h3>Basic Navigation</h3>
            <ul>
                <li>Use the URL bar to enter websites</li>
                <li>Use Back/Forward buttons to navigate history</li>
                <li>Use Ctrl+T to open new tabs</li>
                <li>Use Ctrl+W to close current tab</li>
            </ul>
            <h3>Page Display</h3>
            <ul>
                <li><b>Zoom</b>: Hold Ctrl and scroll mouse wheel up/down to zoom in/out</li>
                <li>Default zoom level is 100%</li>
                <li>Zoom levels are maintained separately for each tab</li>
            </ul>
            <h3>Features</h3>
            <ul>
                <li>Bookmark your favorite pages</li>
                <li>View browsing history</li>
                <li>View page statistics</li>
                <li>Save pages locally</li>
                <li>Responsive zooming for better readability</li>
                <li>History tracking</li>
                <li>Security-focused navigation</li>
            </ul>
            <p>&copy; 2025 Spidy Project</p>
        """))

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(help_dialog.reject)
        layout.addWidget(button_box)

        help_dialog.setLayout(layout)
        help_dialog.exec()
        
    def get_git_commits(self, count=10):
        """
        Retrieve recent git commits with author, date, and message
        
        Args:
            count: Number of commits to retrieve (default: 10)
            
        Returns:
            List of commit dictionaries with keys: hash, author, date, message
        """
        commits = []
        try:
            # Format: hash, author name, author email, date, subject
            format_str = "--pretty=format:%h|%an|%ae|%ad|%s"
            output = subprocess.check_output(
                ['git', 'log', f'-{count}', format_str, '--date=iso'],
                text=True, stderr=subprocess.PIPE
            ).strip()
            
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split('|', 4)
                    if len(parts) >= 5:
                        commit = {
                            'hash': parts[0],
                            'author': f"{parts[1]} <{parts[2]}>",
                            'date': parts[3],
                            'message': parts[4]
                        }
                        commits.append(commit)
        except Exception as e:
            print(f"Error retrieving git commits: {e}")
        
        return commits
        
    def get_git_tags(self):
        """
        Retrieve git tags (releases) with dates
        
        Returns:
            List of tag dictionaries with keys: name, date, commit_hash
        """
        tags = []
        try:
            # First get all tags
            tag_output = subprocess.check_output(
                ['git', 'tag'],
                text=True, stderr=subprocess.PIPE
            ).strip()
            
            if not tag_output:
                return tags
                
            # For each tag, get its date and commit hash
            for tag_name in tag_output.split('\n'):
                tag_info = subprocess.check_output(
                    ['git', 'show', '--format=%h|%ad', '--date=iso', tag_name],
                    text=True, stderr=subprocess.PIPE
                ).strip().split('\n')[0]
                
                parts = tag_info.split('|')
                if len(parts) >= 2:
                    tags.append({
                        'name': tag_name,
                        'commit_hash': parts[0],
                        'date': parts[1]
                    })
        except Exception as e:
            print(f"Error retrieving git tags: {e}")
            
        return tags

    def get_github_repo_url(self):
        """Attempt to get the GitHub repository URL if available"""
        try:
            remote_url = subprocess.check_output(
                ['git', 'config', '--get', 'remote.origin.url'],
                text=True, stderr=subprocess.PIPE
            ).strip()
            
            # Convert SSH URL to HTTPS if needed
            if remote_url.startswith('git@github.com:'):
                repo_path = remote_url.split('git@github.com:')[1].replace('.git', '')
                return f"https://github.com/{repo_path}"
            elif 'github.com' in remote_url:
                return remote_url.replace('.git', '')
            
            return None
        except Exception:
            return None

    def show_about(self):
        """Show about dialog with application information"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Spidy")
        about_dialog.resize(400, 400)  # Slightly larger for the new button
        
        # Try to get git commit information
        last_commit = "Unknown"
        try:
            last_commit = subprocess.check_output(
                ['git', 'log', '-1', '--format=%cd', '--date=iso'],
                text=True, stderr=subprocess.PIPE
            ).strip()
        except:
            pass  # Silently handle any errors
            
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>Spidy Web Browser</h2>"))
        layout.addWidget(QLabel(f"""
            <p style="text-align: center;">
                <b>Version:</b> 1.0.0<br>
                <b>Author:</b> Spidy Project Team<br>
                <b>License:</b> MIT
            </p>
            
            <p>
                A standards-based, open-source web browser built with Python and PyQt6.
                Provides browsing functionality, bookmarks, history tracking, and statistics.
            </p>
            
            <h3>Features</h3>
            <ul>
                <li>Multiple tab support</li>
                <li>Bookmark management</li>
                <li>Browsing history</li>
                <li>Markdown file rendering</li>
                <li>Page zoom functionality</li>
                <li>Security-focused navigation</li>
            </ul>
            
            <p>Last Commit: {last_commit}</p>
            <p>Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>&copy; 2025 Spidy Project</p>
        """))
        
        # Add button to view commit history
        history_button = QPushButton("View Commit and Release History")
        history_button.clicked.connect(self.show_release_history)
        layout.addWidget(history_button)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(about_dialog.reject)
        layout.addWidget(button_box)
        
        about_dialog.setLayout(layout)
        about_dialog.exec()
        
    def show_release_history(self):
        """Show detailed commit and release history"""
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("Spidy Commit and Release History")
        history_dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Add heading
        layout.addWidget(QLabel("<h2>Spidy Browser Commit and Release History</h2>"))
        
        # Get repository URL if available
        repo_url = self.get_github_repo_url()
        if repo_url:
            link_label = QLabel(f'<p>Repository: <a href="{repo_url}">{repo_url}</a></p>')
            link_label.setOpenExternalLinks(True)
            layout.addWidget(link_label)
        
        # Add releases section if tags exist
        tags = self.get_git_tags()
        if tags:
            layout.addWidget(QLabel("<h3>Release History</h3>"))
            
            releases_text = "<ul>"
            for tag in tags:
                releases_text += f"""
                    <li>
                        <b>{tag['name']}</b> ({tag['date']})<br>
                        <span style="color: #666; font-family: monospace;">Commit: {tag['commit_hash']}</span>
                    </li>
                """
            releases_text += "</ul>"
            
            layout.addWidget(QLabel(releases_text))
        else:
            layout.addWidget(QLabel("<p>No release tags found in the repository.</p>"))
        
        # Add commit history section
        commits = self.get_git_commits(20)  # Get 20 most recent commits
        
        if commits:
            layout.addWidget(QLabel("<h3>Recent Commits</h3>"))
            
            # Create a widget to hold the commits
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            
            # Generate commit history HTML
            commits_html = "<ul style='margin-left: 0; padding-left: 15px;'>"
            for commit in commits:
                # Create a clean display of the commit info with styling
                commit_url = f"{repo_url}/commit/{commit['hash']}" if repo_url else None
                
                if commit_url:
                    hash_display = f"""<a href="{commit_url}" style="font-family: monospace; 
                                       text-decoration: none; color: #0366d6;">{commit['hash']}</a>"""
                else:
                    hash_display = f"""<span style="font-family: monospace; color: #666;">
                                      {commit['hash']}</span>"""
                    
                commits_html += f"""
                    <li style="margin-bottom: 10px;">
                        <div>
                            <b>{commit['message']}</b><br>
                            {hash_display} - <span style="color: #666;">{commit['date']}</span><br>
                            <span style="color: #0b0;">Author:</span> {commit['author']}
                        </div>
                    </li>
                """
            commits_html += "</ul>"
            commits_label = QLabel(commits_html)
            commits_label.setOpenExternalLinks(True)
            commits_label.setWordWrap(True)
            scroll_layout.addWidget(commits_label)
            
            # Create a scroll area for the commits
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(scroll_content)
            scroll_area.setMinimumHeight(250)
            layout.addWidget(scroll_area)
        else:
            layout.addWidget(QLabel("<p>No commit history found or unable to retrieve commits.</p>"))
        
        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(history_dialog.reject)
        layout.addWidget(button_box)
        
        history_dialog.setLayout(layout)
        history_dialog.exec()
