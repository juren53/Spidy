#!/usr/bin/env python3
"""
Diagnostic script for Spidy browser hyperlink recognition issues
This script helps identify and fix issues with the JAUs-Startup-Page hyperlinks in Spidy browser.
"""

import os
import re
import shutil
import argparse
import subprocess
from pathlib import Path

# Configuration
SOURCE_HTML = "/home/juren/Projects/JAUs-Startup-Page/index.html"
OUTPUT_DIR = "/home/juren/Projects/Spidy/link_tests"
LOG_FILE = os.path.join(OUTPUT_DIR, "link_test_log.txt")


def setup_environment():
    """Create output directory and initialize the testing environment"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize log file
    with open(LOG_FILE, "w") as f:
        f.write("Spidy Browser Hyperlink Diagnostic Log\n")
        f.write("=====================================\n\n")
        f.write(f"Original file: {SOURCE_HTML}\n")
        f.write(f"Output directory: {OUTPUT_DIR}\n\n")


def clean_html(input_file, output_file):
    """
    Clean the HTML file by removing excessive whitespace
    
    Args:
        input_file: Path to the original HTML file
        output_file: Path to write the cleaned HTML file
    
    Returns:
        tuple: (original_size, cleaned_size) in bytes
    """
    print(f"Cleaning HTML file: {input_file} -> {output_file}")
    
    # Read the original file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_size = len(content)
    
    # Clean up excessive whitespace before function definitions
    # This pattern looks for lines with excessive spaces followed by JavaScript functions
    cleaned_content = re.sub(
        r'(\s{50,})([a-zA-Z_][a-zA-Z0-9_]*\s*\()',
        r'\n    \2',
        content
    )
    
    # Clean up whitespace before closing script tags
    cleaned_content = re.sub(
        r'(\s{50,})(</script>)',
        r'\n    \2',
        cleaned_content
    )
    
    # Clean up whitespace in script blocks (multiple spaces to single space)
    cleaned_content = re.sub(
        r'(<script[^>]*>)(\s{50,})',
        r'\1\n    ',
        cleaned_content
    )
    
    # Write the cleaned content to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(cleaned_content)
    
    cleaned_size = len(cleaned_content)
    
    # Log the results
    with open(LOG_FILE, "a") as f:
        f.write(f"Original file size: {original_size} bytes\n")
        f.write(f"Cleaned file size: {cleaned_size} bytes\n")
        f.write(f"Reduced by: {original_size - cleaned_size} bytes ({100 * (original_size - cleaned_size) / original_size:.2f}%)\n\n")
    
    return original_size, cleaned_size


def add_debug_code(input_file, output_file):
    """
    Add JavaScript debugging code to the HTML file to track link clicks
    
    Args:
        input_file: Path to the HTML file
        output_file: Path to write the modified HTML file
    """
    print(f"Adding debug code to: {input_file} -> {output_file}")
    
    # Read the input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Create the debug JavaScript
    debug_script = """
    <script>
    // Spidy Browser Diagnostic Script
    console.log('Spidy Browser Diagnostic Script loaded');
    
    // Store original document.write to fix potential issues
    const originalDocWrite = document.write;
    
    // Override document.write to log it
    document.write = function() {
        console.log('document.write called with:', arguments);
        return originalDocWrite.apply(document, arguments);
    };
    
    // Track all link clicks
    document.addEventListener('click', function(event) {
        // Traverse up to find the clicked link
        let target = event.target;
        while (target && target.tagName !== 'A') {
            target = target.parentElement;
        }
        
        // If we clicked on a link, log details
        if (target && target.tagName === 'A') {
            const href = target.getAttribute('href') || 'no-href';
            const targetAttr = target.getAttribute('target') || 'no-target';
            const baseTag = document.querySelector('base');
            const baseTarget = baseTag ? baseTag.getAttribute('target') : 'no-base-target';
            
            console.log('LINK CLICKED: ' + href);
            console.log('  Link target: ' + targetAttr);
            console.log('  Base target: ' + baseTarget);
            console.log('  Link HTML: ' + target.outerHTML);
            
            // Create a visible notification for debugging
            const notification = document.createElement('div');
            notification.style.position = 'fixed';
            notification.style.top = '10px';
            notification.style.right = '10px';
            notification.style.backgroundColor = 'rgba(0, 0, 255, 0.8)';
            notification.style.color = 'white';
            notification.style.padding = '10px';
            notification.style.borderRadius = '5px';
            notification.style.zIndex = '10000';
            notification.innerHTML = 'Link clicked:<br>Href: ' + href + '<br>Target: ' + targetAttr;
            document.body.appendChild(notification);
            
            // Remove notification after 3 seconds
            setTimeout(function() {
                document.body.removeChild(notification);
            }, 3000);
        }
    }, true);
    
    // Log when page is fully loaded
    window.addEventListener('load', function() {
        console.log('Page fully loaded');
        
        // Check for base tag
        const baseTag = document.querySelector('base');
        if (baseTag) {
            console.log('Base tag found: ' + baseTag.outerHTML);
        } else {
            console.log('No base tag found in the document');
        }
        
        // Count and report links
        const links = document.querySelectorAll('a[href]');
        console.log('Found ' + links.length + ' links on the page');
        
        // Show link diagnostic information
        const diagnostic = document.createElement('div');
        diagnostic.style.position = 'fixed';
        diagnostic.style.bottom = '10px';
        diagnostic.style.right = '10px';
        diagnostic.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        diagnostic.style.color = 'white';
        diagnostic.style.padding = '10px';
        diagnostic.style.borderRadius = '5px';
        diagnostic.style.zIndex = '10000';
        diagnostic.innerHTML = 'Spidy Diagnostic:<br>' + links.length + ' links on this page<br>' + 
            (baseTag ? 'Base target: ' + baseTag.getAttribute('target') : 'No base tag');
        document.body.appendChild(diagnostic);
    });
    </script>
    """
    
    # Add the debug script at the end of the <head> section
    modified_content = content.replace("</head>", debug_script + "\n</head>")
    
    # Write the modified content to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    # Log the modification
    with open(LOG_FILE, "a") as f:
        f.write(f"Added debug script to track link clicks in: {output_file}\n\n")


def create_test_variants():
    """Create several test variants of the HTML file for comparison"""
    # 1. Original file as reference
    original_reference = os.path.join(OUTPUT_DIR, "original.html")
    shutil.copy(SOURCE_HTML, original_reference)
    
    # 2. Original with debugging code added
    original_with_debug = os.path.join(OUTPUT_DIR, "original_debug.html")
    add_debug_code(original_reference, original_with_debug)
    
    # 3. Cleaned file (whitespace removed)
    cleaned_file = os.path.join(OUTPUT_DIR, "cleaned.html")
    clean_html(SOURCE_HTML, cleaned_file)
    
    # 4. Cleaned file with debugging code
    cleaned_with_debug = os.path.join(OUTPUT_DIR, "cleaned_debug.html")
    add_debug_code(cleaned_file, cleaned_with_debug)
    
    # 5. Create a variant with the base tag removed
    no_base_file = os.path.join(OUTPUT_DIR, "no_base_tag.html")
    with open(cleaned_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove the base tag
    modified_content = re.sub(r'<base\s+[^>]*>', '', content)
    with open(no_base_file, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    # Add debug code to the no-base variant
    no_base_with_debug = os.path.join(OUTPUT_DIR, "no_base_tag_debug.html")
    add_debug_code(no_base_file, no_base_with_debug)
    
    # 6. Create simple test case file
    simple_test_file = create_test_case_file()
    
    # Create HTML file listing all test variants
    create_test_index(
        [
            ("Simple Test Case", simple_test_file),
            ("Original HTML", original_with_debug), 
            ("Cleaned HTML (whitespace removed)", cleaned_with_debug),
            ("HTML without base tag", no_base_with_debug)
        ]
    )


def create_test_index(variants):
    """Create an HTML file that links to all test variants"""
    index_file = os.path.join(OUTPUT_DIR, "index.html")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Spidy Browser Link Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .variant {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            .instructions {
                background-color: #ffffcc;
                padding: 10px;
                border-left: 3px solid #ffcc00;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <h1>Spidy Browser Link Test</h1>
        
        <div class="instructions">
            <h3>Instructions:</h3>
            <p>This page contains links to different variants of the JAUs-Startup-Page to test hyperlink recognition in Spidy browser.</p>
            <p>Click on each variant and test if links are working properly. Debug information will be displayed in browser console.</p>
        </div>
        
        <h2>Test Variants:</h2>
    """
    
    for name, path in variants:
        rel_path = os.path.basename(path)
        html_content += f"""
        <div class="variant">
            <h3>{name}</h3>
            <p>Test if hyperlinks work correctly in this variant.</p>
            <p><a href="{rel_path}">Open {rel_path}</a></p>
        </div>
        """
    
    html_content += """
        <div class="instructions">
            <h3>Notes:</h3>
            <ul>
                <li>The original file may have excessive whitespace in JavaScript sections.</li>
                <li>The cleaned file has excessive whitespace removed.</li>
                <li>The no-base-tag variant has the &lt;base target="_blank"&gt; tag removed.</li>
                <li>All variants include diagnostic JavaScript to track link clicks.</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Created test index at: {index_file}")
    with open(LOG_FILE, "a") as f:
        f.write(f"Created test index at: {index_file}\n")
        f.write(f"The index links to {len(variants)} test variants.\n\n")


def launch_browser(url=None):
    """Launch Spidy browser for testing, optionally opening a specific URL"""
    browser_path = "./main.py"
    
    if url:
        full_url = f"file://{url}" if not url.startswith("http") else url
        cmd = ["python3", browser_path, full_url]
    else:
        cmd = ["python3", browser_path]
    
    print(f"Launching Spidy browser: {' '.join(cmd)}")
    
    try:
        # Launch the browser in a new process
        subprocess.Popen(cmd)
        
        with open(LOG_FILE, "a") as f:
            f.write(f"Launched Spidy browser with command: {' '.join(cmd)}\n")
        
        return True
    except Exception as e:
        print(f"Error launching browser: {e}")
        
        with open(LOG_FILE, "a") as f:
            f.write(f"Error launching browser: {e}\n")
        
        return False


def compare_cleaned_with_original():
    """
    Compare the original and cleaned HTML files and report differences
    
    This function analyzes the structure of both files to identify
    key differences that might affect hyperlink behavior.
    """
    original_file = os.path.join(OUTPUT_DIR, "original.html")
    cleaned_file = os.path.join(OUTPUT_DIR, "cleaned.html")
    
    print(f"Comparing original and cleaned HTML files")
    
    # Read both files
    with open(original_file, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    with open(cleaned_file, "r", encoding="utf-8") as f:
        cleaned_content = f.read()
        
    # Basic size comparison
    original_size = len(original_content)
    cleaned_size = len(cleaned_content)
    
    # Count links in both files
    original_links = len(re.findall(r'<a\s+[^>]*href=["\'][^"\']*["\']', original_content))
    cleaned_links = len(re.findall(r'<a\s+[^>]*href=["\'][^"\']*["\']', cleaned_content))
    
    # Check for base tag
    original_base = re.search(r'<base\s+[^>]*target=["\']([^"\']*)["\']', original_content)
    cleaned_base = re.search(r'<base\s+[^>]*target=["\']([^"\']*)["\']', cleaned_content)
    
    # Log the results
    with open(LOG_FILE, "a") as f:
        f.write("Comparison of Original vs Cleaned HTML:\n")
        f.write(f"Original size: {original_size} bytes\n")
        f.write(f"Cleaned size: {cleaned_size} bytes\n")
        f.write(f"Size reduction: {original_size - cleaned_size} bytes ({100 * (original_size - cleaned_size) / original_size:.2f}%)\n\n")
        
        f.write(f"Original file links: {original_links}\n")
        f.write(f"Cleaned file links: {cleaned_links}\n")
        
        f.write(f"Original base tag: {original_base.group(1) if original_base else 'Not found'}\n")
        f.write(f"Cleaned base tag: {cleaned_base.group(1) if cleaned_base else 'Not found'}\n\n")
    
    return {
        "original_size": original_size,
        "cleaned_size": cleaned_size,
        "original_links": original_links,
        "cleaned_links": cleaned_links,
        "original_base": original_base.group(1) if original_base else None,
        "cleaned_base": cleaned_base.group(1) if cleaned_base else None
    }


def create_test_case_file():
    """Create a simple HTML test case file with a base tag and links"""
    test_case_file = os.path.join(OUTPUT_DIR, "simple_test.html")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Simple Link Test</title>
        <base target="_blank">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .link-section {
                margin: 20px 0;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            h2 {
                margin-top: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            .debug-panel {
                position: fixed;
                bottom: 10px;
                right: 10px;
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                max-width: 300px;
                z-index: 1000;
            }
            .notification {
                position: fixed;
                top: 10px;
                right: 10px;
                background-color: rgba(0, 0, 255, 0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                z-index: 1001;
                font-size: 14px;
                display: none;
            }
        </style>
        <script>
            // Track link clicks
            document.addEventListener('click', function(event) {
                let target = event.target;
                while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                }
                
                if (target && target.tagName === 'A') {
                    // Get link attributes
                    const href = target.getAttribute('href') || 'no-href';
                    const targetAttr = target.getAttribute('target') || 'none';
                    
                    // Get base tag info
                    const baseElement = document.querySelector('base');
                    const baseTarget = baseElement ? baseElement.getAttribute('target') : 'none';
                    
                    // Log link details to console
                    console.log('LINK CLICKED:', {
                        href: href,
                        linkTarget: targetAttr,
                        baseTarget: baseTarget,
                        html: target.outerHTML
                    });
                    
                    // Display notification
                    const notification = document.getElementById('click-notification');
                    notification.innerHTML = `
                        <div>Link clicked:</div>
                        <div>URL: ${href}</div>
                        <div>Link target: ${targetAttr}</div>
                        <div>Base target: ${baseTarget}</div>
                    `;
                    notification.style.display = 'block';
                    
                    // Hide notification after 3 seconds
                    setTimeout(function() {
                        notification.style.display = 'none';
                    }, 3000);
                }
            }, true);
            
            // Initialize debug info when page loads
            window.addEventListener('load', function() {
                const baseElement = document.querySelector('base');
                const baseInfo = baseElement 
                    ? `Base tag found: target="${baseElement.getAttribute('target')}"`
                    : 'No base tag found';
                
                const debugPanel = document.getElementById('debug-panel');
                debugPanel.innerHTML = `
                    <div><strong>Spidy Link Test</strong></div>
                    <div>${baseInfo}</div>
                    <div>Link test page ready</div>
                    <div>Click links to test behavior</div>
                `;
            });
        </script>
    </head>
    <body>
        <h1>Spidy Browser Link Test</h1>
        
        <p>This page tests how Spidy browser handles links in an HTML document with <code>&lt;base target="_blank"&gt;</code>.</p>
        
        <h2>HTTP/HTTPS Links</h2>
        <div class="link-section">
            <p><a href="https://www.google.com/">Google</a> - Standard https link (should open in new tab due to base tag)</p>
            <p><a href="http://example.com/">Example.com</a> - Standard http link (should open in new tab due to base tag)</p>
            <p><a href="https://github.com/" target="_self">GitHub (explicit _self target)</a> - Has target="_self" (should override base tag)</p>
        </div>

        <h2>File and Local Links</h2>
        <div class="link-section">
            <p><a href="index.html">Back to Test Index</a> - Relative link to index.html</p>
            <p><a href="/home/juren/Projects/Spidy/README.md">Local Markdown File</a> - Absolute path (file link)</p>
            <p><a href="file:///home/juren/Projects/Spidy/README.md">Explicit file:// Protocol</a> - With file:// prefix</p>
        </div>

        <h2>Special Links</h2>
        <div class="link-section">
            <p><a href="#section1">Jump to Section 1</a> - Fragment link (should navigate in same page)</p>
            <p><a href="mailto:test@example.com">Email Link</a> - mailto: protocol</p>
            <p><a href="about:config">about:config</a> - about: protocol</p>
        </div>

        <h2 id="section1">Section 1</h2>
        <div class="link-section">
            <p>This is Section 1, a target for the fragment link above.</p>
            <p><a href="javascript:alert('test')">JavaScript Link</a> - javascript: protocol (may be blocked)</p>
            <p><a href="http://192.168.1.1/">Local network link</a> - Internal IP address</p>
        </div>

        <!-- Debug elements -->
        <div id="debug-panel" class="debug-panel"></div>
        <div id="click-notification" class="notification"></div>
    </body>
    </html>
    """
    
    with open(test_case_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Created simple test case file: {test_case_file}")
    with open(LOG_FILE, "a") as f:
        f.write(f"Created simple test case file: {test_case_file}\n\n")
    
    # Add this test case to the index as well
    return test_case_file


def main():
    """Main function to run the diagnostic script"""
    parser = argparse.ArgumentParser(
        description="Diagnose and fix hyperlink recognition issues in Spidy browser"
    )
    parser.add_argument(
        "--no-browser", 
        action="store_true", 
        help="Don't launch browser automatically"
    )
    parser.add_argument(
        "--original-only", 
        action="store_true", 
        help="Only test the original HTML file"
    )
    parser.add_argument(
        "--clean-only", 
        action="store_true", 
        help="Only create a cleaned version without testing"
    )
    args = parser.parse_args()
    
    try:
        print("Spidy Browser Hyperlink Diagnostic Tool")
        print("======================================\n")
        
        # Set up the testing environment
        setup_environment()
        print("Testing environment set up successfully\n")
        
        # Create test variants
        create_test_variants()
        print("Created test variants successfully\n")
        
        # Compare cleaned and original files
        comparison = compare_cleaned_with_original()
        print(f"Original file size: {comparison['original_size']} bytes")
        print(f"Cleaned file size: {comparison['cleaned_size']} bytes")
        print(f"Size reduction: {comparison['original_size'] - comparison['cleaned_size']} bytes")
        print(f"Links found in original: {comparison['original_links']}")
        print(f"Links found in cleaned: {comparison['cleaned_links']}\n")
        
        # Get index file path
        index_file = os.path.join(OUTPUT_DIR, "index.html")
        
        # Launch browser if not disabled
        if not args.no_browser:
            print("Launching Spidy browser with test page...")
            launch_browser(index_file)
            print(f"\nDiagnostic tool has been set up at {OUTPUT_DIR}")
            print("Follow the instructions in the browser to test hyperlink behavior\n")
        else:
            print(f"\nTest environment prepared at {OUTPUT_DIR}")
            print(f"You can manually open {index_file} in Spidy browser to test\n")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

