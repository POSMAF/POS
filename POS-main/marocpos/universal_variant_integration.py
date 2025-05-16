#!/usr/bin/env python3
"""
Universal Variant System Integration

This script provides a universal way to integrate the variant system
with any UI framework. It creates a standalone variant manager that
can be launched from any application.

Usage:
    python universal_variant_integration.py

Features:
1. Creates a simple bridge file that works with any UI framework
2. Initializes the variant system database
3. Provides functions to launch the variant manager
"""

import os
import sys
import shutil

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Variant bridge file content
VARIANT_BRIDGE_CONTENT = """
#!/usr/bin/env python3
\"\"\"
Variant System Bridge

This module provides a bridge between any UI framework and the variant system.
It allows launching the variant manager as a separate process or window.
\"\"\"

import os
import sys
import subprocess

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the variant system
from variant_system import initialize

# Initialize the database tables
def init_db():
    \"\"\"Initialize the variant system database tables\"\"\"
    try:
        initialize()
        return True
    except Exception as e:
        print(f"Error initializing variant system: {e}")
        return False

# Launch the variant manager as a separate process
def launch_variant_manager(product_id):
    \"\"\"
    Launch the variant manager for a product as a separate process
    
    Args:
        product_id: The product ID to manage variants for
    \"\"\"
    try:
        # Path to Python and the example script
        python_path = sys.executable
        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "variant_system_example.py"
        )
        
        # Launch the process
        subprocess.Popen([python_path, script_path, str(product_id)])
        return True
    except Exception as e:
        print(f"Error launching variant manager: {e}")
        return False

# Open the variant dialog directly
def open_variant_dialog(product_id):
    \"\"\"
    Open the variant dialog for a product
    
    Args:
        product_id: The product ID to manage variants for
        
    Returns:
        True if successful, False otherwise
    \"\"\"
    try:
        # Import the simple UI
        from variant_system.simple_ui import show_variant_dialog
        
        # Import Qt for the dialog
        from PyQt5.QtWidgets import QApplication
        
        # Create application instance if needed
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # Show the dialog
        show_variant_dialog(product_id, None)
        return True
    except Exception as e:
        print(f"Error opening variant dialog: {e}")
        # Try falling back to the separate process method
        return launch_variant_manager(product_id)

# For direct testing
if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # If product ID is provided, open the variant manager
    if len(sys.argv) > 1:
        try:
            product_id = int(sys.argv[1])
            open_variant_dialog(product_id)
        except ValueError:
            print(f"Invalid product ID: {sys.argv[1]}")
            print("Usage: python variant_bridge.py [product_id]")
    else:
        print("Usage: python variant_bridge.py [product_id]")
        print("No product ID provided. Run with a product ID to open the variant manager.")
"""

# Modified example script content to handle arguments
EXAMPLE_SCRIPT_MODIFICATION = """
# Add this at the bottom of the script to support direct product opening
if __name__ == "__main__" and len(sys.argv) > 1:
    app = QApplication(sys.argv)
    try:
        product_id = int(sys.argv[1])
        # Open directly to the variant management for this product
        from variant_system.simple_ui import show_variant_dialog
        show_variant_dialog(product_id, None)
    except Exception as e:
        print(f"Error: {e}")
    sys.exit(0)
"""

def create_bridge_file():
    """Create the variant bridge file"""
    bridge_path = os.path.join(BASE_DIR, "variant_bridge.py")
    
    try:
        with open(bridge_path, 'w', encoding='utf-8') as f:
            f.write(VARIANT_BRIDGE_CONTENT)
        
        # Make it executable
        os.chmod(bridge_path, 0o755)
        
        print(f"✅ Created variant bridge file at {bridge_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating variant bridge file: {e}")
        return False

def modify_example_script():
    """Modify the example script to handle arguments"""
    example_path = os.path.join(BASE_DIR, "variant_system_example.py")
    
    if not os.path.exists(example_path):
        print(f"❌ Error: Example script not found at {example_path}")
        return False
    
    # Create backup
    backup_path = os.path.join(BASE_DIR, "variant_system_example.py.backup")
    try:
        shutil.copy2(example_path, backup_path)
        print(f"✅ Created backup of example script at {backup_path}")
        
        # Check if already modified
        with open(example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "if __name__ == \"__main__\" and len(sys.argv) > 1:" in content:
            print("✅ Example script already modified")
            return True
        
        # Append the modification
        with open(example_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + EXAMPLE_SCRIPT_MODIFICATION)
        
        print(f"✅ Modified example script to handle command line arguments")
        return True
    except Exception as e:
        print(f"❌ Error modifying example script: {e}")
        return False

def create_integration_guide():
    """Create an integration guide file"""
    guide_path = os.path.join(BASE_DIR, "variant_integration_guide.txt")
    
    guide_content = """
VARIANT SYSTEM INTEGRATION GUIDE
===============================

This guide provides instructions for integrating the variant system with your application.

OPTION 1: UNIVERSAL INTEGRATION (WORKS WITH ANY UI FRAMEWORK)
-----------------------------------------------------------

1. Initialize the variant system database in your main.py:

   ```python
   # At the start of your application
   from variant_bridge import init_db
   init_db()
   ```

2. Add a "Manage Variants" button to your product page, and connect it to:

   ```python
   from variant_bridge import launch_variant_manager
   
   def open_variant_manager():
       product_id = get_current_product_id()  # Your function to get the current product ID
       launch_variant_manager(product_id)
   ```

OPTION 2: DIRECT INTEGRATION (FOR PyQt5/PySide APPLICATIONS)
----------------------------------------------------------

If your application uses PyQt5 or PySide, you can directly integrate the variant system:

1. Initialize the variant system in your main.py:

   ```python
   from variant_system import initialize
   initialize()
   ```

2. Add a button to open the variant manager:

   ```python
   from variant_system.simple_ui import show_variant_dialog
   
   def open_variant_manager():
       product_id = get_current_product_id()  # Your function to get the current product ID
       show_variant_dialog(product_id, self)  # 'self' is your parent window
   ```

TESTING THE INTEGRATION
---------------------

You can test the variant system by running:

```
python variant_bridge.py [product_id]
```

Replace [product_id] with the ID of a product in your database.

TROUBLESHOOTING
-------------

If you encounter any issues:

1. Database errors: Make sure to call init_db() before using any variant system functions

2. UI framework errors: Use OPTION 1 if you're not using PyQt5/PySide

3. Missing product: Make sure the product exists in the database before opening the variant manager
"""
    
    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✅ Created integration guide at {guide_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating integration guide: {e}")
        return False

def main():
    """Main function"""
    print("=== Universal Variant System Integration ===")
    print("This will create files to help you integrate the variant system with any UI framework.")
    
    # Create bridge file
    create_bridge_file()
    
    # Modify example script
    modify_example_script()
    
    # Create integration guide
    create_integration_guide()
    
    print("\n=== Integration Complete! ===")
    print("The universal variant integration is now ready to use.")
    print("You can now launch the variant manager from any application.")
    print("\nIntegration options:")
    print("1. Use 'variant_bridge.py' to launch the variant manager from any UI framework")
    print("2. See 'variant_integration_guide.txt' for detailed instructions")
    print("\nExample usage:")
    print("python variant_bridge.py [product_id]")

if __name__ == "__main__":
    main()
