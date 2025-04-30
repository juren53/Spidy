from PyQt5.QtCore import QUrl

def test_url(url_string):
    print(f"\nTesting URL: {url_string}")
    # Create QUrl directly
    qurl1 = QUrl(url_string)
    print(f"Direct QUrl:")
    print(f"  Scheme: {qurl1.scheme()}")
    print(f"  Host: {qurl1.host()}")
    print(f"  Path: {qurl1.path()}")
    print(f"  Is valid: {qurl1.isValid()}")
    print(f"  Is local file: {qurl1.isLocalFile()}")
    print(f"  ToString: {qurl1.toString()}")
    
    # Test with current browser logic
    modified = url_string
    if not modified.startswith("http"):
        modified = "http://" + modified
    
    qurl2 = QUrl(modified)
    print(f"With browser logic (adding http:// if needed):")
    print(f"  Modified string: {modified}")
    print(f"  Scheme: {qurl2.scheme()}")
    print(f"  Host: {qurl2.host()}")
    print(f"  Path: {qurl2.path()}")
    print(f"  Is valid: {qurl2.isValid()}")
    print(f"  Is local file: {qurl2.isLocalFile()}")
    print(f"  ToString: {qurl2.toString()}")

# Test various URL formats
test_url("www.example.com")
test_url("http://www.example.com")
test_url("https://www.example.com")
test_url("file:///home/juren/Projects/Spidy/webpage.html")
test_url("/home/juren/Projects/Spidy/webpage.html")
test_url("file://localhost/home/juren/Projects/Spidy/webpage.html")

