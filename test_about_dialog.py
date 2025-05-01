#!/usr/bin/env python3
"""
Test script for Spidy Browser's About dialog functionality.
This script initializes a QApplication, creates a Browser instance,
and calls the show_about method to verify it works correctly.
"""

import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Import the Browser class from the current directory
from browser import Browser

def get_git_commit_date():
    """Get the last git commit date directly for verification"""
    try:
        last_commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%cd', '--date=iso'],
            text=True, stderr=subprocess.PIPE
        ).strip()
        return last_commit
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Error retrieving git commit date: {e}")
        return "Not available"

def main():
    # First, verify the git commit date directly
    print(f"Git commit date directly from git: {get_git_commit_date()}")
    
    try:
        # Initialize a QApplication instance (required for any Qt GUI application)
        app = QApplication(sys.argv)
        
        # Create a Browser instance
        browser = Browser()
        
        # Set up a timer to call the show_about method after the browser has fully initialized
        # This ensures the browser window is visible before showing the dialog
        QTimer.singleShot(500, browser.show_about)
        
        # Set up another timer to exit the application after 5 seconds
        # This allows enough time to view the About dialog but ensures the script terminates
        QTimer.singleShot(5000, app.quit)
        
        print("Opening About dialog. It will close automatically in 5 seconds...")
        
        # Start the Qt event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

