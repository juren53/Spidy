# Spidy Bookmark Manager

A standalone GUI application for managing bookmarks for the Spidy web browser.

## Features

- View all bookmarks in a table format
- Add new bookmarks
- Edit existing bookmark titles and URLs
- Delete bookmarks
- Reorder bookmarks by moving them up and down in the list
- Save changes back to the Spidy bookmarks.json file

## Requirements

- Python 3.8 or higher
- PyQt6

## Installation

1. Make sure you have Python and PyQt6 installed:
   ```
   pip install PyQt6
   ```

2. Make the script executable:
   ```
   chmod +x spidy_bookmark_manager.py
   ```

## Usage

### Running the Application

```bash
./spidy_bookmark_manager.py
```

or

```bash
python spidy_bookmark_manager.py
```

### Managing Bookmarks

- **Add**: Create a new bookmark with a title and URL
- **Edit**: Modify the title or URL of an existing bookmark
- **Delete**: Remove a bookmark from the list
- **Move Up/Down**: Change the position of a bookmark in the list
- **Save**: Write all changes back to the bookmarks.json file

## File Location

The application works with the Spidy browser's bookmarks file located at:
```
~/.spidy/bookmarks.json
```

Changes are not saved automatically - you must click the "Save" button to persist your changes.

## Keyboard Navigation

- Use arrow keys to navigate the bookmark table
- Press Enter or double-click to edit the selected bookmark
- Use Tab to navigate between fields in the edit dialog

## Troubleshooting

If you encounter errors when running the application:

1. Ensure the ~/.spidy directory exists
2. Check that bookmarks.json is a valid JSON file
3. Make sure you have the correct permissions to read/write the file

## Development

This is a simple PyQt6 application that can be extended with additional features such as:

- Import/export of bookmarks from other browsers
- Bookmark categorization and folders
- Search functionality
- Drag and drop reordering

## License

MIT License
