# Spidy Browser Test Sequence

This document outlines a systematic sequence of manual tests to verify the functionality of Spidy Browser.

## Prerequisites

1. Make sure all required dependencies are installed:
   ```
   pip install PyQt5 PyQtWebEngine
   ```

2. Start the browser:
   ```
   python main.py
   ```

## 1. Tab Management Tests

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1a | Press Ctrl+T | New tab should open with default search page |
| 1b | Type "python.org" in URL bar and press Enter | Browser should navigate to Python's website |
| 1c | Press Ctrl+T again | Third tab should open |
| 1d | Navigate to "github.com" in third tab | Browser should load GitHub's website |
| 1e | Press Ctrl+Tab multiple times | Should cycle through all open tabs in order |
| 1f | Select middle tab and press Ctrl+W | Middle tab should close, leaving two tabs |

## 2. Navigation Tests

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2a | Click back button | Should navigate back to previous page |
| 2b | Click forward button | Should navigate forward to next page |
| 2c | Click File → Open File, select README.md | Should display README content in browser |
| 2d | Type "wikipedia.org" in URL bar | Should navigate to Wikipedia |
| 2e | Click reload button | Current page should refresh |

## 3. Bookmark Tests

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3a | Navigate to "python.org" | Should display Python website |
| 3b | Click Bookmarks → Add Bookmark | Confirmation dialog should appear |
| 3c | Navigate to "github.com" | Should display GitHub website |
| 3d | Click Bookmarks → Add Bookmark | Confirmation dialog should appear |
| 3e | Click Bookmarks → View Bookmarks | Bookmark manager dialog should appear with both bookmarks |
| 3f | Double-click on a bookmark | Should navigate to the bookmarked page |
| 3g | Open bookmark manager, select a bookmark, click Remove | Selected bookmark should be removed |
| 3h | Click Close on bookmark manager | Dialog should close |

## 4. Feature Tests

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4a | Click Statistics → View Statistics | Statistics dialog should appear |
| 4b | Verify statistics content | Should show page size, links count, etc. |
| 4c | Close dialog, click Help → Help Contents | Help dialog should appear |
| 4d | Verify help information | Should display browser usage instructions |
| 4e | Close dialog, click About → About Spidy | About dialog should appear |
| 4f | Verify about information | Should display version and copyright info |

## 5. History Tests

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5a | Click History → View History | History dialog should appear with navigation history |
| 5b | Verify previous navigations | Should list all pages visited during testing |
| 5c | Double-click on a history item | Should navigate to that page |
| 5d | Open history again, click Clear History | Confirmation dialog should appear |
| 5e | Confirm clear | History should be emptied |

## 6. Save/Load Tests

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6a | Navigate to any webpage | Page should load |
| 6b | Click File → Save Page | Save dialog should appear |
| 6c | Choose location and save | Confirmation dialog should appear when complete |
| 6d | Click File → Open File | Open dialog should appear |
| 6e | Select the saved file | Should display the saved page content |

## Test Completion

When all tests have been completed, exit the browser by closing the window or selecting File → Exit.

Notes:
- Configuration files are stored in ~/.spidy/
- Test results can be verified by checking bookmarks.json and history.json in this directory

