import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile

# Create QApplication first to avoid the error
app = QApplication(sys.argv)

# Get the default profile 
default_profile = QWebEngineProfile.defaultProfile()
print("Default profile methods:")
for name in dir(default_profile):
    if not name.startswith('_') and not callable(getattr(default_profile, name)):
        print(f"  {name}")

# Check if there's a settings method and what it provides
if hasattr(default_profile, 'settings'):
    settings = default_profile.settings()
    print("\nProfile settings methods:")
    for name in dir(settings):
        if not name.startswith('_') and not callable(getattr(settings, name)):
            print(f"  {name}")
