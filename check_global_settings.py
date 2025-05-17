import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineCore import QWebEngineGlobalSettings

# Print all available methods in QWebEngineGlobalSettings
print("Available QWebEngineGlobalSettings methods:")
for name in dir(QWebEngineGlobalSettings):
    if not name.startswith('_'):
        print(name)
