"""
UI Manager for Spidy Web Browser

Handles UI setup, menus, and dialogs.
"""

from PyQt5.QtCore import QDateTime, QSize
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMenuBar, QMenu, QAction, QShortcut, QLabel,
    QDialog, QGridLayout, QDialogButtonBox
)

class UIManager:
    def __init__(self, browser):
        self.browser = browser
        self.setup_ui()

    def setup_ui(self):
        """Initialize the main UI components"""
        self.browser.setWindowTitle('Spidy Web Browser')
        self.browser.setWindowIcon(QIcon('ICON_spidy.jpeg'))
        self.browser.setGeometry(100, 100, 800, 600)
        
        # Create central widget and main layout
        self.main_layout = QVBoxLayout()
        
        # Setup UI components
        self.setup_navigation_bar()
        self.create_menu()
        self.setup_shortcuts()

        # Add components to main layout
        self.main_layout.addLayout(self.nav_layout)
        self.main_layout.addWidget(self.browser.tab_manager.tab_widget)
        
        # Set layout on browser's central widget
        self.browser.central_widget.setLayout(self.main_layout)

    def setup_navigation_bar(self):
        """Setup the navigation bar with URL field and buttons"""
        self.nav_layout = QHBoxLayout()
        
        # Create navigation controls
        self.browser.url_field = QLineEdit()
        self.browser.back_button = QPushButton('Back')
        self.browser.forward_button = QPushButton('Forward')
        self.browser.go_button = QPushButton('Go')
        self.browser.reload_button = QPushButton('Reload')
        
        # Connect navigation buttons
        self.browser.go_button.clicked.connect(self.browser.navigation_manager.navigate_to_url)
        self.browser.back_button.clicked.connect(self.browser.navigation_manager.view_back)
        self.browser.forward_button.clicked.connect(self.browser.navigation_manager.view_forward)
        self.browser.reload_button.clicked.connect(self.browser.navigation_manager.reload_page)
        self.browser.url_field.returnPressed.connect(self.browser.navigation_manager.navigate_to_url)
        
        # Initialize with disabled navigation buttons
        self.browser.back_button.setEnabled(False)
        self.browser.forward_button.setEnabled(False)
        
        # Add controls to navigation layout
        self.nav_layout.addWidget(self.browser.back_button)
        self.nav_layout.addWidget(self.browser.forward_button)
        self.nav_layout.addWidget(self.browser.reload_button)
        self.nav_layout.addWidget(self.browser.url_field)
        self.nav_layout.addWidget(self.browser.go_button)

    def create_menu(self):
        """Create and setup the main menu bar"""
        menu_bar = self.browser.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        self.add_file_menu_actions(file_menu)
        
        # Bookmarks menu
        bookmarks_menu = menu_bar.addMenu("&Bookmarks")
        self.add_bookmark_menu_actions(bookmarks_menu)
        
        # History menu
        history_menu = menu_bar.addMenu("&History")
        self.add_history_menu_actions(history_menu)
        
        # Other menus
        self.add_additional_menus(menu_bar)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+T"), self.browser, self.browser.tab_manager.add_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self.browser, self.browser.tab_manager.close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self.browser, self.browser.tab_manager.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self.browser, self.browser.tab_manager.previous_tab)

    def add_file_menu_actions(self, menu):
        """Add actions to File menu"""
        open_file_action = QAction("Open File", self.browser)
        menu.addAction(open_file_action)
        open_file_action.triggered.connect(self.browser.open_file)
        
        save_page_action = QAction('Save Page', self.browser)
        menu.addAction(save_page_action)
        save_page_action.triggered.connect(self.browser.save_page)
        
        menu.addSeparator()
        exit_action = QAction("E&xit", self.browser)
        menu.addAction(exit_action)
        exit_action.triggered.connect(self.browser.close)

    def add_bookmark_menu_actions(self, menu):
        """Add actions to Bookmarks menu"""
        add_bookmark_action = QAction("Add Bookmark", self.browser)
        view_bookmarks_action = QAction("View Bookmarks", self.browser)
        clear_bookmarks_action = QAction("Clear Bookmarks", self.browser)
        
        menu.addAction(add_bookmark_action)
        menu.addAction(view_bookmarks_action)
        menu.addAction(clear_bookmarks_action)
        
        add_bookmark_action.triggered.connect(self.browser.bookmark_manager.add_bookmark)
        view_bookmarks_action.triggered.connect(self.browser.bookmark_manager.view_bookmarks)
        clear_bookmarks_action.triggered.connect(self.browser.bookmark_manager.clear_bookmarks)

    def add_history_menu_actions(self, menu):
        """Add actions to History menu"""
        view_history_action = QAction("View History", self.browser)
        clear_history_action = QAction("Clear History", self.browser)
        
        menu.addAction(view_history_action)
        menu.addAction(clear_history_action)
        
        view_history_action.triggered.connect(self.browser.navigation_manager.view_history)
        clear_history_action.triggered.connect(self.browser.navigation_manager.clear_history)

    def add_additional_menus(self, menu_bar):
        """Add additional menus (Statistics, Help, About)"""
        # Statistics menu
        stats_menu = menu_bar.addMenu("&Statistics")
        view_stats_action = QAction("View Statistics", self.browser)
        stats_menu.addAction(view_stats_action)
        view_stats_action.triggered.connect(self.browser.view_statistics)
        
        # Help menu
        help_menu = menu_bar.addMenu("Hel&p")
        help_content_action = QAction("Help Contents", self.browser)
        help_menu.addAction(help_content_action)
        help_content_action.triggered.connect(self.browser.show_help)
        
        # About menu
        about_menu = menu_bar.addMenu("&About")
        about_action = QAction("About Spidy", self.browser)
        about_menu.addAction(about_action)
        about_action.triggered.connect(self.browser.show_about)

