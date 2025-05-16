#!/usr/bin/env python3
"""
Variant System Integration for Add Product Dialog

This script automatically patches the add_product_dialog.py file
to replace the existing variant UI with the new variant system.

Usage:
    python integrate_variants_to_add_product.py

After running:
1. The add_product_dialog.py file is backed up
2. The file is modified to use the new variant system
3. The integration is ready to use
"""

import os
import sys
import shutil
import re

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADD_PRODUCT_PATH = os.path.join(BASE_DIR, "ui", "add_product_dialog.py")
BACKUP_PATH = os.path.join(BASE_DIR, "ui", "add_product_dialog.py.backup")

# Integration code to be inserted
IMPORT_CODE = """
# Variant system imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from variant_system import initialize
"""

INIT_VARIANT_SYSTEM_CODE = """
        # Initialize variant system database tables
        initialize()
"""

VARIANT_BUTTON_CODE = """
        # Variant management button
        self.variant_btn = QPushButton("Gérer les variantes")
        self.variant_btn.setStyleSheet(
            "background-color: #5e72e4; color: white; font-weight: bold; padding: 8px 15px;"
        )
        self.variant_btn.setEnabled(False)  # Enabled after product is saved
        self.variant_btn.clicked.connect(self.open_variant_manager)
"""

VARIANT_MANAGER_CODE = """
    def open_variant_manager(self):
        \"\"\"Open the variant manager for this product\"\"\"
        if not hasattr(self, 'product_id') or not self.product_id:
            QMessageBox.warning(
                self,
                "Produit non enregistré",
                "Veuillez d'abord enregistrer le produit pour gérer ses variantes."
            )
            return
        
        try:
            # Open the variant manager
            from variant_system.simple_ui import show_variant_dialog
            show_variant_dialog(self.product_id, self)
        except Exception as e:
            print(f"Error opening variant manager: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture du gestionnaire de variantes: {str(e)}"
            )
"""

SAVE_PRODUCT_CODE = """
        # Store the product ID for variant management
        self.product_id = product_id
        
        # Enable variant management button
        if hasattr(self, 'variant_btn'):
            self.variant_btn.setEnabled(True)
"""

def backup_file():
    """Create a backup of the add_product_dialog.py file"""
    if not os.path.exists(ADD_PRODUCT_PATH):
        print(f"❌ Error: Could not find {ADD_PRODUCT_PATH}")
        return False
    
    shutil.copy2(ADD_PRODUCT_PATH, BACKUP_PATH)
    print(f"✅ Created backup at {BACKUP_PATH}")
    return True

def patch_file():
    """Patch the add_product_dialog.py file with variant system integration"""
    if not os.path.exists(ADD_PRODUCT_PATH):
        print(f"❌ Error: Could not find {ADD_PRODUCT_PATH}")
        return False
    
    try:
        with open(ADD_PRODUCT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add imports
        import_pattern = r'import .*?\n\n'
        match = re.search(import_pattern, content, re.DOTALL)
        if match:
            pos = match.end()
            content = content[:pos] + IMPORT_CODE + content[pos:]
        else:
            print("⚠️ Warning: Could not find import section, adding at the top")
            content = IMPORT_CODE + content
        
        # Add initialization in __init__
        init_pattern = r'def __init__\(.*?\):(.*?)self\.init_ui\('
        match = re.search(init_pattern, content, re.DOTALL)
        if match:
            pos = match.end()
            content = content[:pos] + INIT_VARIANT_SYSTEM_CODE + content[pos:]
        else:
            print("⚠️ Warning: Could not find __init__ method")
        
        # Add variant button in init_ui
        ui_pattern = r'def init_ui\(.*?\):(.*?)# Connect signals'
        match = re.search(ui_pattern, content, re.DOTALL)
        if match:
            pos = match.end()
            content = content[:pos] + VARIANT_BUTTON_CODE + content[pos:]
        else:
            print("⚠️ Warning: Could not find init_ui method")
        
        # Add variant manager method
        class_end_pattern = r'\n\n# .*'
        match = re.search(class_end_pattern, content)
        if match:
            pos = match.start()
            content = content[:pos] + VARIANT_MANAGER_CODE + content[pos:]
        else:
            # Try to add at the end of the file
            content += "\n" + VARIANT_MANAGER_CODE
        
        # Modify save_product method to enable variant button
        save_pattern = r'def save_product\(.*?\):(.*?)(?:return|self\.close\(\))'
        match = re.search(save_pattern, content, re.DOTALL)
        if match:
            # Look for successful product save (product_id assignment)
            save_content = match.group(1)
            product_id_pattern = r'product_id = .*?[\n,)]'
            id_match = re.search(product_id_pattern, save_content)
            
            if id_match:
                pos = match.start(1) + id_match.end()
                content = content[:pos] + SAVE_PRODUCT_CODE + content[pos:]
            else:
                print("⚠️ Warning: Could not find product_id assignment in save_product method")
        else:
            print("⚠️ Warning: Could not find save_product method")
        
        # Write modified content
        with open(ADD_PRODUCT_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully patched {ADD_PRODUCT_PATH}")
        return True
    
    except Exception as e:
        print(f"❌ Error patching file: {e}")
        return False

def main():
    """Main function"""
    print("=== Integrating Variant System to Add Product Dialog ===")
    
    # Confirm before proceeding
    confirm = input("This will modify your add_product_dialog.py file. Continue? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Create backup
    if not backup_file():
        print("❌ Failed to create backup. Aborting.")
        return
    
    # Patch file
    if patch_file():
        print("\n=== Integration Complete! ===")
        print("The variant system has been integrated into your add product dialog.")
        print("You can now manage variants directly from the product creation screen.")
        print(f"\nIf you need to restore the original file, you can find a backup at: {BACKUP_PATH}")
    else:
        print("\n❌ Integration failed.")
        print(f"You can restore from the backup at: {BACKUP_PATH}")

if __name__ == "__main__":
    main()
