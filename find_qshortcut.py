import sys
import inspect

try:
    # Try common modules that might contain QShortcut
    from PyQt6 import QtWidgets, QtGui, QtCore
    
    # Check in QtGui
    print("Looking in QtGui...")
    gui_members = [name for name in dir(QtGui) if name.startswith('Q')]
    print(f"Found {len(gui_members)} classes starting with Q")
    
    # Specifically look for QShortcut
    if 'QShortcut' in dir(QtWidgets):
        print("\nQShortcut found in QtWidgets")
    elif 'QShortcut' in dir(QtGui):
        print("\nQShortcut found in QtGui")
    elif 'QShortcut' in dir(QtCore):
        print("\nQShortcut found in QtCore")
    else:
        print("\nQShortcut not found in common modules")
        
    # Print all classes from QtGui that have 'Short' in their name
    print("\nClasses in QtGui with 'Short' in their name:")
    for name in gui_members:
        if 'Short' in name:
            print(f"- {name}")
    
except ImportError as e:
    print(f"Import error: {e}")
    
