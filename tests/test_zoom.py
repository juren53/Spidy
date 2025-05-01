#!/usr/bin/env python3
"""
Test script for WebEngineView zoom functionality.

This script creates a test window with a WebEngineView to verify
that the zoom functionality works correctly with Ctrl+mouse wheel.
"""

import os
import sys
import time

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import QUrl, Qt
from web_view import WebEngineView

class ZoomTestWindow(QMainWindow):
    """Test window for zoom functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zoom Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create WebEngineView
        self.web_view = WebEngineView()
        main_layout.addWidget(self.web_view)
        
        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # Add zoom indicator
        self.zoom_label = QLabel("Zoom: 100%")
        control_layout.addWidget(self.zoom_label)
        
        # Add zoom control buttons
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_btn)
        
        reset_zoom_btn = QPushButton("Reset Zoom")
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        control_layout.addWidget(reset_zoom_btn)
        
        main_layout.addWidget(control_panel)
        
        # Load test content
        self.load_test_content()
        
        # Update zoom indicator when the window is shown
        self.show()
        self.update_zoom_indicator()
        
    def load_test_content(self):
        """Load HTML content with different text sizes"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zoom Test Page</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    line-height: 1.6;
                }
                .instructions {
                    background-color: #f0f0f0;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .small-text {
                    font-size: 10px;
                }
                .normal-text {
                    font-size: 16px;
                }
                .large-text {
                    font-size: 24px;
                }
                .very-large-text {
                    font-size: 36px;
                }
                section {
                    margin-bottom: 20px;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="instructions">
                <h2>Zoom Test Page</h2>
                <p>This page demonstrates the zoom functionality. You can:</p>
                <ul>
                    <li>Hold Ctrl and scroll the mouse wheel to zoom in/out</li>
                    <li>Use the buttons below to control zoom</li>
                </ul>
            </div>
            
            <section>
                <h3>Small Text (10px)</h3>
                <p class="small-text">This is small text that might be difficult to read without zooming in.</p>
            </section>
            
            <section>
                <h3>Normal Text (16px)</h3>
                <p class="normal-text">This is normal text at the default size most websites use.</p>
            </section>
            
            <section>
                <h3>Large Text (24px)</h3>
                <p class="large-text">This is large text that's easier to read.</p>
            </section>
            
            <section>
                <h3>Very Large Text (36px)</h3>
                <p class="very-large-text">This is very large text.</p>
            </section>
        </body>
        </html>
        """
        
        # Load the HTML content
        self.web_view.setHtml(html_content, QUrl("file://"))
        
    def zoom_in(self):
        """Zoom in and update indicator"""
        self.web_view.zoom_in()
        self.update_zoom_indicator()
        
    def zoom_out(self):
        """Zoom out and update indicator"""
        self.web_view.zoom_out()
        self.update_zoom_indicator()
        
    def reset_zoom(self):
        """Reset zoom and update indicator"""
        self.web_view.reset_zoom()
        self.update_zoom_indicator()
        
    def update_zoom_indicator(self):
        """Update the zoom level indicator"""
        zoom_factor = self.web_view.get_zoom_factor()
        self.zoom_label.setText(f"Zoom: {int(zoom_factor * 100)}%")
        print(f"Current zoom level: {int(zoom_factor * 100)}%")

    def wheelEvent(self, event):
        """Display a message when Ctrl+wheel is used"""
        if event.modifiers() & Qt.ControlModifier:
            print("Ctrl+wheel detected in main window (wheel event is handled by the WebEngineView)")
        super().wheelEvent(event)

def main():
    """Run the zoom test"""
    print("Starting Zoom Functionality Test")
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = ZoomTestWindow()
    window.show()
    
    # Run the application
    exit_code = app.exec_()
    
    # Report results
    print("Zoom test completed")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())

