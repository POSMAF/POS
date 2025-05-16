#!/usr/bin/env python3
"""
Automatic Patch Script for Adding Variant Dashboard to Main Application

This script automatically patches your main.py file to add the variant dashboard
functionality directly to your main application without requiring manual code changes.

Usage:
    python patch_main_for_variants.py

After running:
1. Your application will have a "Manage Variants" button on product screens
2. You'll be able to create and modify variants directly
3. No manual code changes required
"""

import os
import sys
import shutil
import re
import importlib.util
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QPushButton, QMainWindow
)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Path to main.py
MAIN_PY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
BACKUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py.backup")

# Patch content to add to main.py
PATCH_CONTENT = """
# === BEGIN VARIANT DASHBOARD INTEGRATION ===
def add_variant_dashboard_to_windows():
    \"\"\"Add variant dashboard functionality to all relevant windows\"\"\"
    try:
        # Import necessary modules
        from ui.variant_dashboard import VariantDashboard
        from PyQt5.QtWidgets import QPushButton, QMessageBox
        
        # Function to open dashboard for a product
        def open_dashboard_for_product(product_id, parent=None):
            try:
                dashboard = VariantDashboard(product_id, parent)
                dashboard.exec_()
            except Exception as e:
                print(f"Error opening dashboard: {e}")
                QMessageBox.critical(
                    parent,
                    "Erreur",
                    f"Erreur lors de l'ouverture du tableau de bord: {str(e)}"
                )
        
        # Add button to product management window
        def patch_product_management():
            try:
                from ui.product_management_window import ProductManagementWindow
                
                # Store original __init__ method
                original_init = ProductManagementWindow.__init__
                
                # Define patched __init__ method
                def patched_init(self, *args, **kwargs):
                    # Call original __init__
                    original_init(self, *args, **kwargs)
                    
                    # Add variant management button
                    try:
                        # Create button
                        variant_btn = QPushButton("🧩 Gérer les variantes")
                        variant_btn.setStyleSheet(\"\"\"
                            QPushButton {
                                background-color: #5e72e4;
                                color: white;
                                font-weight: bold;
                                padding: 8px 15px;
                                border-radius: 4px;
                            }
                            QPushButton:hover {
                                background-color: #324cdd;
                            }
                        \"\"\")
                        
                        # Connect button to function
                        variant_btn.clicked.connect(lambda: manage_variants(self))
                        
                        # Add button to layout
                        layout_added = False
                        
                        # Try adding to various layouts
                        if hasattr(self, 'layout') and callable(self.layout):
                            main_layout = self.layout()
                            if main_layout:
                                main_layout.addWidget(variant_btn)
                                layout_added = True
                        
                        if not layout_added and hasattr(self, 'button_layout'):
                            self.button_layout.addWidget(variant_btn)
                            layout_added = True
                            
                        if not layout_added:
                            # Last resort - add to self directly
                            variant_btn.setParent(self)
                            variant_btn.move(10, 10)
                            variant_btn.show()
                            
                    except Exception as e:
                        print(f"Error adding variant button: {e}")
                
                # Function to open dashboard from product window
                def manage_variants(window):
                    try:
                        # Get selected product
                        selected_product = None
                        
                        if hasattr(window, 'products_table'):
                            table = window.products_table
                            selected_items = table.selectedItems()
                            
                            if selected_items:
                                row = selected_items[0].row()
                                id_item = table.item(row, 0)
                                
                                if id_item:
                                    product_id = int(id_item.text())
                                    open_dashboard_for_product(product_id, window)
                                    return
                        
                        # If no product selected
                        QMessageBox.warning(
                            window,
                            "Aucun produit sélectionné",
                            "Veuillez sélectionner un produit dans la liste pour gérer ses variantes."
                        )
                    except Exception as e:
                        print(f"Error managing variants: {e}")
                        QMessageBox.critical(
                            window,
                            "Erreur",
                            f"Erreur lors de l'ouverture du gestionnaire de variantes: {str(e)}"
                        )
                
                # Replace original __init__ with patched version
                ProductManagementWindow.__init__ = patched_init
                print("✅ Successfully patched product management window")
                
            except Exception as e:
                print(f"❌ Error patching product management window: {e}")
        
        # Patch edit product dialog
        def patch_edit_product_dialog():
            try:
                from ui.edit_product_dialog import EditProductDialog
                
                # Store original __init__ method
                original_init = EditProductDialog.__init__
                
                # Define patched __init__ method
                def patched_init(self, product, *args, **kwargs):
                    # Call original __init__
                    original_init(self, product, *args, **kwargs)
                    
                    # Add variant management button
                    try:
                        # Create button
                        variant_btn = QPushButton("🧩 Gérer les variantes")
                        variant_btn.setStyleSheet(\"\"\"
                            QPushButton {
                                background-color: #5e72e4;
                                color: white;
                                font-weight: bold;
                                padding: 8px 15px;
                                border-radius: 4px;
                            }
                            QPushButton:hover {
                                background-color: #324cdd;
                            }
                        \"\"\")
                        
                        # Store product ID
                        product_id = product.get('id')
                        
                        # Connect button to function
                        variant_btn.clicked.connect(
                            lambda: open_dashboard_for_product(product_id, self)
                        )
                        
                        # Try to add button to various layouts
                        layout_added = False
                        
                        # Try button layout first
                        for attr_name in ['button_layout', 'buttons_layout']:
                            if hasattr(self, attr_name):
                                layout = getattr(self, attr_name)
                                layout.addWidget(variant_btn)
                                layout_added = True
                                break
                        
                        # Try main layout if no button layout
                        if not layout_added and hasattr(self, 'layout') and callable(self.layout):
                            self.layout().addWidget(variant_btn)
                            layout_added = True
                        
                        # Last resort - add to dialog directly
                        if not layout_added:
                            variant_btn.setParent(self)
                            variant_btn.move(10, 10)
                            variant_btn.show()
                            
                    except Exception as e:
                        print(f"Error adding variant button to dialog: {e}")
                
                # Replace original __init__ with patched version
                EditProductDialog.__init__ = patched_init
                print("✅ Successfully patched edit product dialog")
                
            except Exception as e:
                print(f"❌ Error patching edit product dialog: {e}")
                import traceback
                traceback.print_exc()
        
        # Apply patches
        patch_product_management()
        patch_edit_product_dialog()
        
    except Exception as e:
        print(f"❌ Error in variant dashboard integration: {e}")
        import traceback
        traceback.print_exc()

# Call the function to add variant dashboard
add_variant_dashboard_to_windows()
# === END VARIANT DASHBOARD INTEGRATION ===
"""

def backup_main_py():
    """Create a backup of main.py"""
    if os.path.exists(MAIN_PY_PATH):
        shutil.copy2(MAIN_PY_PATH, BACKUP_PATH)
        print(f"✅ Created backup of main.py at {BACKUP_PATH}")
        return True
    else:
        print(f"❌ main.py not found at {MAIN_PY_PATH}")
        return False

def patch_main_py():
    """Patch main.py to add variant dashboard integration"""
    if not os.path.exists(MAIN_PY_PATH):
        print(f"❌ main.py not found at {MAIN_PY_PATH}")
        return False
    
    try:
        # Read current content
        with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already patched
        if "=== BEGIN VARIANT DASHBOARD INTEGRATION ===" in content:
            print("⚠️ main.py is already patched!")
            return True
        
        # Find appropriate place to add patch
        # Look for a good insertion point (just before the app.exec_ line)
        match = re.search(r'app\.exec_\(\)', content)
        if match:
            # Insert before app.exec_()
            pos = match.start()
            new_content = content[:pos] + PATCH_CONTENT + "\n" + content[pos:]
        else:
            # If app.exec_() not found, add to the end
            new_content = content + "\n" + PATCH_CONTENT
        
        # Write patched content
        with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Successfully patched main.py with variant dashboard integration")
        return True
        
    except Exception as e:
        print(f"❌ Error patching main.py: {e}")
        return False

def check_dependencies():
    """Check if necessary dependencies are available"""
    missing = []
    
    # Check PyQt5
    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5")
    
    # Check database connection
    try:
        from database import get_connection
        conn = get_connection()
        if not conn:
            missing.append("database connection")
    except Exception:
        missing.append("database module")
    
    return missing

def main():
    """Main function to patch the application"""
    print("=== Variant Dashboard Integration Patcher ===")
    print("This will add variant management functionality to your main application")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install the required dependencies before continuing")
        return
    
    # Confirm before proceeding
    confirm = input("This will modify your main.py file to add variant dashboard functionality. Proceed? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Create backup
    if not backup_main_py():
        print("❌ Failed to create backup. Aborting.")
        return
    
    # Patch main.py
    if patch_main_py():
        print("\n=== Patch Applied Successfully! ===")
        print("Your application now has variant management functionality.")
        print("When you run your application, you'll see a '🧩 Gérer les variantes' button")
        print("on the product management and edit product screens.")
        print(f"\nIf you need to restore the original file, you can find a backup at: {BACKUP_PATH}")
    else:
        print("\n❌ Failed to apply patch.")
        print(f"You can manually restore from the backup at: {BACKUP_PATH}")

if __name__ == "__main__":
    main()
