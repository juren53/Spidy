from PyQt6.QtWebEngineCore import QWebEnginePage
import inspect

# Print all NavigationType enum values
for name in dir(QWebEnginePage.NavigationType):
    if not name.startswith('_'):
        print(f"{name} = {getattr(QWebEnginePage.NavigationType, name)}")

