import sys
#pip install PyQt
from PyQt5.QtCore import QUrl
#pip install PyQtWebEngine
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QApplication, QLineEdit, QPushButton, QVBoxLayout, QWidget

class Browser(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Simple Web Browser')
        self.setGeometry(100, 100, 800, 600)
        
        self.url_field = QLineEdit(self)
        self.go_button = QPushButton('Go', self)
        self.go_button.clicked.connect(self.navigate_to_url)
        
        self.view = QWebEngineView(self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.url_field)
        layout.addWidget(self.go_button)
        layout.addWidget(self.view)
        
        self.show()
    
    def navigate_to_url(self):
        url = self.url_field.text()
        if not url.startswith('http'):
            url = 'http://' + url
        self.view.setUrl(QUrl(url))

app = QApplication(sys.argv)
browser = Browser()
sys.exit(app.exec_())
