from PyQt5.QtCore import QUrl
print("Testing URL handling:")
test_url = "file:///home/juren/Projects/Spidy/webpage.html"
print(f"Original URL: {test_url}")
if not test_url.startswith("http"):
    test_url = "http://" + test_url
print(f"Modified URL: {test_url}")
qurl = QUrl(test_url)
print(f"QUrl scheme: {qurl.scheme()}")
print(f"QUrl is valid: {qurl.isValid()}")
print(f"QUrl path: {qurl.path()}")

