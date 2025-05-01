import sys
#pip install PyQt
from PyQt5.QtCore import QUrl
#pip install PyQtWebEngine
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QApplication, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget

class Browser(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Simple Web Browser')
        self.setGeometry(100, 100, 800, 600)
        
        self.url_field = QLineEdit(self)
        self.back_button = QPushButton('Back', self)
        self.forward_button = QPushButton('Forward', self)
        self.go_button = QPushButton('Go', self)
        
        # Connect navigation buttons
        self.go_button.clicked.connect(self.navigate_to_url)
        self.back_button.clicked.connect(self.view_back)
        self.forward_button.clicked.connect(self.view_forward)
        
        # Initialize with disabled navigation buttons
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        
        self.view = QWebEngineView(self)
        
        # Create horizontal layout for navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.forward_button)
        nav_layout.addWidget(self.url_field)
        nav_layout.addWidget(self.go_button)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.addLayout(nav_layout)
        layout.addWidget(self.view)
        
        # Connect navigation signals after view is set up
        self.setup_navigation_connections()
        
        self.show()
    
    def navigate_to_url(self):
        url = self.url_field.text()
        if not url.startswith('http'):
            url = 'http://' + url
        self.view.setUrl(QUrl(url))
    
    def view_back(self):
        self.view.back()
        
    def view_forward(self):
        self.view.forward()
        
    def setup_navigation_connections(self):
        # Connect navigation signals to enable/disable buttons
        self.view.loadFinished.connect(self.update_navigation_buttons)
        self.view.urlChanged.connect(lambda: self.update_navigation_buttons())
        
    def update_navigation_buttons(self):
        self.back_button.setEnabled(self.view.page().history().canGoBack())
        self.forward_button.setEnabled(self.view.page().history().canGoForward())

app = QApplication(sys.argv)
browser = Browser()
sys.exit(app.exec_())
