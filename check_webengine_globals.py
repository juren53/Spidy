import sys
from PyQt6 import QtWebEngineCore

# Print all types in QtWebEngineCore that might have global settings
print("Searching for global settings related classes:")
for name in dir(QtWebEngineCore):
    if name.startswith('Q') and ('Global' in name or 'Default' in name):
        print(f"Found: {name}")
    elif 'Settings' in name:
        print(f"Settings related: {name}")

# Check if QWebEngineProfile has default profile method
if hasattr(QtWebEngineCore.QWebEngineProfile, 'defaultProfile'):
    print("\nQWebEngineProfile has defaultProfile method")
    
    # Get the default profile and check if it has settings method
    try:
        default_profile = QtWebEngineCore.QWebEngineProfile.defaultProfile()
        print("Successfully got defaultProfile()")
        
        if hasattr(default_profile, 'settings'):
            print("defaultProfile has a settings() method")
    except Exception as e:
        print(f"Error getting defaultProfile: {e}")
    
