import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineCore import QWebEngineSettings

# Print all available methods in QWebEngineSettings
print("Available QWebEngineSettings methods:")
for name in dir(QWebEngineSettings):
    if not name.startswith('_'):
        print(name)
