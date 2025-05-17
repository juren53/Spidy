    def createWindow(self, window_type):
        """
        Override createWindow to handle opening links in new tabs.
        
        This method is automatically called when a link needs to be opened in a new 
        window/tab, such as when a user right-clicks on a link and selects "Open Link in New Tab".
        
        Args:
            window_type: The type of window to create
            
        Returns:
            A WebEngineView instance for the new tab
        """
        print(f"RIGHT-CLICK: createWindow called with type {window_type}")
        
        # Find the browser that has a tab_manager
        browser = None
        parent = self.parent()
        
        # Approach 1: Traverse parent hierarchy
        while parent:
            print(f"Checking parent: {parent}")
            if hasattr(parent, 'tab_manager'):
                browser = parent
                break
            parent = parent.parent()
        
        # Approach 2: Look for the browser in top-level widgets
        if not browser:
            from PyQt6.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'tab_manager'):
                    browser = widget
                    print(f"Found browser in top-level widgets: {browser}")
                    break
        
        # If browser is found, use its tab_manager to create a new tab
        if browser:
            print(f"Using browser.tab_manager: {browser.tab_manager}")
            new_tab = browser.tab_manager.add_new_tab()
            print(f"Created new tab: {new_tab}")
            return new_tab
        
        # If all else fails, create a new WebEngineView directly
        print("Could not find browser, creating standalone WebEngineView")
        new_view = WebEngineView()
        return new_view
