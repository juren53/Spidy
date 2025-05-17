import sys
import inspect

try:
    # Try common modules that might contain QAction
    from PyQt6 import QtWidgets, QtGui, QtCore

    # Check in QtWidgets
    print("Looking in QtWidgets...")
    widgets_members = [name for name in dir(QtWidgets) if name.startswith('Q')]
    print(f"Found {len(widgets_members)} widgets starting with Q")
    print("Example widgets:", widgets_members[:5])
    
    # Check in QtGui
    print("\nLooking in QtGui...")
    gui_members = [name for name in dir(QtGui) if name.startswith('Q')]
    print(f"Found {len(gui_members)} classes starting with Q")
    print("Example classes:", gui_members[:5])
    
    # Specifically look for QAction
    if 'QAction' in dir(QtWidgets):
        print("\nQAction found in QtWidgets")
    elif 'QAction' in dir(QtGui):
        print("\nQAction found in QtGui")
    elif 'QAction' in dir(QtCore):
        print("\nQAction found in QtCore")
    else:
        print("\nQAction not found in common modules")
    
except ImportError as e:
    print(f"Import error: {e}")
    
