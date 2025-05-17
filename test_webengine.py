import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

app = QApplication(sys.argv)
window = QMainWindow()
view = QWebEngineView()
view.load(QUrl("https://www.google.com"))
window.setCentralWidget(view)
window.show()
sys.exit(app.exec())
