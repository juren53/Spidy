#!/usr/bin/env python3
"""
Test script for the Markdown to HTML conversion functionality.

This script tests the markdown conversion functionality directly,
without going through the browser interface.
"""

import os
import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication

# Import the LinkHandler class from link_handler.py
from link_handler import LinkHandler

def main():
    """Test the Markdown to HTML conversion functionality."""
    print("Testing Markdown to HTML conversion...")
    
    # Create a QApplication instance (required for LinkHandler)
    app = QApplication(sys.argv)
    
    # Create a LinkHandler instance
    link_handler = LinkHandler()
    
    # Path to the test Markdown file
    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    print(f"Using Markdown file: {md_path}")
    
    if not os.path.exists(md_path):
        print(f"Error: Markdown file not found at {md_path}")
        return 1
    
    # Get file size and first few lines for debugging
    file_size = os.path.getsize(md_path)
    print(f"File size: {file_size} bytes")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        first_lines = [next(f) for _ in range(5)]
    print("First 5 lines of Markdown file:")
    for line in first_lines:
        print(f"  {line.rstrip()}")
    
    try:
        # Convert Markdown to HTML
        print("\nConverting Markdown to HTML...")
        html_content = link_handler.convert_markdown_to_html(md_path)
        
        # Display conversion results
        html_size = len(html_content)
        print(f"Conversion successful! HTML size: {html_size} bytes")
        
        # Save HTML to file for inspection
        html_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markdown_output.html")
        with open(html_output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML output saved to: {html_output_path}")
        
        # Extract and print some parts of the HTML for verification
        html_lines = html_content.splitlines()
        print("\nHTML head (first 10 lines):")
        for line in html_lines[:10]:
            print(f"  {line}")
        
        print("\nHTML body start (first few lines of content):")
        body_start_index = next((i for i, line in enumerate(html_lines) if "<body>" in line), -1)
        if body_start_index >= 0:
            for line in html_lines[body_start_index:body_start_index+10]:
                print(f"  {line}")
                
        return 0
    except Exception as e:
        import traceback
        print(f"Error during conversion: {str(e)}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())

