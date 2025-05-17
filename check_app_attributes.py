import sys
from PyQt6.QtCore import Qt

# Print all available ApplicationAttribute enum values
print("Available Qt.ApplicationAttribute values:")
for name in dir(Qt.ApplicationAttribute):
    if not name.startswith('_'):
        print(name)
