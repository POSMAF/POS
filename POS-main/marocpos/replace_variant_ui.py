#!/usr/bin/env python3
"""
Replace Existing Variant UI

This script completely replaces the existing variant UI in the add_product_dialog.py
with the new variant system, preserving the original look and feel while upgrading
the functionality.

Usage:
    python replace_variant_ui.py
"""

import os
import sys
import shutil
import re

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADD_PRODUCT_PATH = os.path.join(BASE_DIR, "ui", "add_product_dialog.py")
BACKUP_PATH = os.path.join(BASE_DIR, "ui", "add_product_dialog.py.backup")

# Import code to be added at the top of the file
IMPORT_CODE = """
# Variant system imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from variant_system import initialize

# Initialize variant system on import
initialize()
"""

# New variant UI code to replace the existing section
NEW_VARIANT_UI_CODE = """
        # Variants section
        variants_group = QGroupBox("Variantes")
        variants_layout = QVBoxLayout(variants_group)
        
        # Has variants checkbox
        self.has_variants_check = QCheckBox("Article avec variantes")
        self.has_variants_check.toggled.connect(self.toggle_variants_section)
        variants_layout.addWidget(self.has_variants_check)
        
        # Variants section (initially hidden)
        self.variants_section = QWidget()
        self.variants_section.setVisible(False)
        variants_section_layout = QVBoxLayout(self.variants_section)
        variants_section_layout.setContentsMargins(10, 10, 10, 10)
        
        # Attributes section
        attr_label = QLabel("Attributs disponibles")
        attr_label.setStyleSheet("font-weight: bold;")
        variants_section_layout.addWidget(attr_label)
        
        # Attributes frame
        attr_frame = QFrame()
        attr_frame.setFrameShape(QFrame.StyledPanel)
        attr_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")
        attr_layout = QVBoxLayout(attr_frame)
        
        # Load attribute types
        self.attr_checkboxes = {}
        try:
            from variant_system.attribute_manager import AttributeType
            attr_types = AttributeType.get_all()
            
            if attr_types:
                for attr_type in attr_types:
                    cb = QCheckBox(attr_type.display_name)
                    cb.setProperty("attr_id", attr_type.id)
                    self.attr_checkboxes[attr_type.id] = cb
                    attr_layout.addWidget(cb)
            else:
                attr_layout.addWidget(QLabel("Aucun attribut défini dans le système"))
        except Exception as e:
            print(f"Error loading attributes: {e}")
            attr_layout.addWidget(QLabel("Erreur lors du chargement des attributs"))
        
        # Add new attribute input
        add_attr_layout = QHBoxLayout()
        self.new_attr_input = QLineEdit()
        self.new_attr_input.setPlaceholderText("Autre attribut...")
        add_attr_btn = QPushButton("+")
        add_attr_btn.setFixedWidth(30)
        add_attr_btn.clicked.connect(self.add_new_attribute)
        
        add_attr_layout.addWidget(self.new_attr_input)
        add_attr_layout.addWidget(add_attr_btn)
        
        attr_layout.addLayout(add_attr_layout)
        
        # Manage all attributes button
        manage_all_btn = QPushButton("Gérer tous les attributs")
        manage_all_btn.clicked.connect(self.manage_all_attributes)
        attr_layout.addWidget(manage_all_btn)
        
        variants_section_layout.addWidget(attr_frame)
        
        # Status label
        self.variant_status_label = QLabel("Aucune variante configurée")
        self.variant_status_label.setAlignment(Qt.AlignCenter)
        self.variant_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        variants_section_layout.addWidget(self.variant_status_label)
        
        # Manage variants button
        self.manage_variants_btn = QPushButton("Gérer les variantes")
        self.manage_variants_btn.setStyleSheet("background-color: #007bff; color: white;")
        self.manage_variants_btn.clicked.connect(self.manage_variants)
        self.manage_variants_btn.setEnabled(False)  # Enabled after product is saved
        variants_section_layout.addWidget(self.manage_variants_btn)
        
        variants_layout.addWidget(self.variants_section)
        layout.addWidget(variants_group)
"""

# New methods to be added to the class
NEW_VARIANT_METHODS = """
    def toggle_variants_section(self, checked):
        \"\"\"Show/hide the variants section\"\"\"
        self.variants_section.setVisible(checked)
    
    def add_new_attribute(self):
        \"\"\"Add a new attribute\"\"\"
        name = self.new_attr_input.text().strip()
        if not name:
            return
        
        try:
            # Create a new attribute type
            from variant_system.attribute_manager import AttributeType
            attr_type = AttributeType(
                name=name.lower().replace(" ", "_"),
                display_name=name,
                display_type="select"
            )
            
            if attr_type.save():
                # Add checkbox for the new attribute
                cb = QCheckBox(attr_type.display_name)
                cb.setProperty("attr_id", attr_type.id)
                cb.setChecked(True)
                self.attr_checkboxes[attr_type.id] = cb
                
                # Find the attribute frame layout
                for i in range(self.variants_section.layout().count()):
                    item = self.variants_section.layout().itemAt(i)
                    if isinstance(item.widget(), QFrame):
                        # Add the checkbox before the "add new" layout
                        layout = item.widget().layout()
                        layout.insertWidget(layout.count() - 2, cb)
                        break
                
                # Clear the input
                self.new_attr_input.clear()
                
                # Show a success message
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Attribut '{name}' ajouté avec succès."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors de l'ajout de l'attribut."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'ajout de l'attribut: {str(e)}"
            )
    
    def manage_all_attributes(self):
        \"\"\"Open attribute manager\"\"\"
        try:
            # Launch attribute manager tab in the example app
            import subprocess
            import sys
            
            python_path = sys.executable
            example_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "variant_system_example.py"
            )
            
            subprocess.Popen([python_path, example_path, "attributes"])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture du gestionnaire d'attributs: {str(e)}"
            )
    
    def manage_variants(self):
        \"\"\"Manage variants for this product\"\"\"
        if not hasattr(self, 'product_id') or not self.product_id:
            # Product not saved yet, we need to save it first
            reply = QMessageBox.question(
                self,
                "Enregistrer le produit",
                "Le produit doit être enregistré avant de gérer les variantes. Voulez-vous l'enregistrer maintenant?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.save_product()
            else:
                return
            
            # If still no product_id, abort
            if not hasattr(self, 'product_id') or not self.product_id:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Erreur lors de l'enregistrement du produit. Impossible de gérer les variantes."
                )
                return
        
        # Add selected attributes to the product
        try:
            from variant_system.attribute_manager import ProductAttribute
            
            # Get selected attributes
            selected_attrs = []
            for attr_id, cb in self.attr_checkboxes.items():
                if cb.isChecked():
                    selected_attrs.append(attr_id)
            
            # Associate attributes with product
            for attr_id in selected_attrs:
                ProductAttribute(
                    product_id=self.product_id,
                    attribute_type_id=attr_id,
                    is_required=True,
                    affects_price=True,
                    affects_inventory=True
                ).save()
            
            # Open the variant manager
            from variant_system.simple_ui import show_variant_dialog
            show_variant_dialog(self.product_id, self)
            
            # Update status label
            self.update_variant_status()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la gestion des variantes: {str(e)}"
            )
    
    def update_variant_status(self):
        \"\"\"Update the variant status label\"\"\"
        if not hasattr(self, 'product_id') or not self.product_id:
            self.variant_status_label.setText("Aucune variante configurée")
            return
        
        try:
            from variant_system.variant_manager import ProductVariant
            
            variants = ProductVariant.get_by_product(self.product_id)
            if variants:
                self.variant_status_label.setText(f"{len(variants)} variantes configurées")
                self.variant_status_label.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                self.variant_status_label.setText("Aucune variante configurée")
                self.variant_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        except Exception as e:
            print(f"Error updating variant status: {e}")
            self.variant_status_label.setText("Erreur lors de la mise à jour")
            self.variant_status_label.setStyleSheet("color: #dc3545;")
"""

# Code to modify the save_product method
SAVE_PRODUCT_UPDATE = """
        # Store the product ID for variant management
        self.product_id = product_id
        
        # Enable variant management button
        if hasattr(self, 'manage_variants_btn'):
            self.manage_variants_btn.setEnabled(True)
            
        # Update variant status
        if hasattr(self, 'update_variant_status'):
            self.update_variant_status()
"""

# Modified example script to handle attribute manager
EXAMPLE_SCRIPT_MODIFICATION = """
# Enable direct launch to attribute manager
if __name__ == "__main__" and len(sys.argv) > 1:
    app = QApplication(sys.argv)
    
    if sys.argv[1] == "attributes":
        # Open directly to the attribute manager tab
        window = VariantSystemExample()
        window.tabs.setCurrentIndex(0)  # Attribute manager tab
        window.show()
        sys.exit(app.exec_())
    else:
        try:
            product_id = int(sys.argv[1])
            # Open directly to the variant management for this product
            from variant_system.simple_ui import show_variant_dialog
            show_variant_dialog(product_id, None)
        except Exception as e:
            print(f"Error: {e}")
        sys.exit(0)
"""

def backup_file():
    """Create a backup of the add_product_dialog.py file"""
    if not os.path.exists(ADD_PRODUCT_PATH):
        print(f"❌ Error: Could not find {ADD_PRODUCT_PATH}")
        return False
    
    shutil.copy2(ADD_PRODUCT_PATH, BACKUP_PATH)
    print(f"✅ Created backup at {BACKUP_PATH}")
    return True

def find_variant_section(content):
    """Find the existing variant section in the file"""
    # Look for various patterns that might indicate the variant section
    patterns = [
        r'# Variants.*?section',
        r'# Variantes',
        r'QGroupBox\([\"\']Variantes',
        r'Article avec variantes'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            # Found a match, now find the start and end of the section
            start_pos = match.start()
            
            # Look for the section before this match to find the actual start
            section_start = content.rfind("        # ", 0, start_pos)
            if section_start == -1:
                section_start = start_pos
            
            # Find the next section after this one
            next_section = content.find("        # ", start_pos + 10)
            if next_section == -1:
                # If no next section, look for the end of the layout
                next_section = content.find("layout.add", start_pos)
                
                # If still not found, look for the end of the init_ui method
                if next_section == -1:
                    next_section = content.find("    def ", start_pos)
            
            if next_section != -1:
                return section_start, next_section
    
    # Could not find the variant section
    return None, None

def patch_file():
    """Patch the add_product_dialog.py file to replace the variant UI"""
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
        
        # Find and replace the variant section
        start_pos, end_pos = find_variant_section(content)
        if start_pos is not None and end_pos is not None:
            # Replace the variant section
            content = content[:start_pos] + NEW_VARIANT_UI_CODE + content[end_pos:]
            print("✅ Replaced variant UI section")
        else:
            # Could not find the variant section, add it before the final button section
            print("⚠️ Warning: Could not find variant section, adding at the end of init_ui")
            # Look for the buttons section or the end of init_ui
            buttons_pos = content.find("        # Buttons", 0)
            if buttons_pos == -1:
                buttons_pos = content.find("    def ", content.find("def init_ui"))
            
            if buttons_pos != -1:
                content = content[:buttons_pos] + NEW_VARIANT_UI_CODE + content[buttons_pos:]
            else:
                print("❌ Error: Could not find a suitable position to add the variant UI")
                return False
        
        # Add new methods
        # Find the end of the class
        class_end_pos = content.rfind("\n\n", 0, content.find("if __name__"))
        if class_end_pos != -1:
            content = content[:class_end_pos] + "\n" + NEW_VARIANT_METHODS + content[class_end_pos:]
            print("✅ Added variant management methods")
        else:
            print("❌ Error: Could not find the end of the class")
            return False
        
        # Modify the save_product method
        save_pattern = r'def save_product\(.*?\):(.*?)(?:return|self\.close\(\))'
        match = re.search(save_pattern, content, re.DOTALL)
        if match:
            # Look for successful product save (product_id assignment)
            save_content = match.group(1)
            product_id_pattern = r'product_id = .*?[\n,)]'
            id_match = re.search(product_id_pattern, save_content)
            
            if id_match:
                pos = match.start(1) + id_match.end()
                content = content[:pos] + SAVE_PRODUCT_UPDATE + content[pos:]
                print("✅ Modified save_product method")
            else:
                print("⚠️ Warning: Could not find product_id assignment in save_product method")
        else:
            print("⚠️ Warning: Could not find save_product method")
        
        # Write modified content
        with open(ADD_PRODUCT_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Successfully patched add_product_dialog.py")
        
        # Modify the example script to handle attributes tab
        example_path = os.path.join(BASE_DIR, "variant_system_example.py")
        if os.path.exists(example_path):
            try:
                # Read example script
                with open(example_path, 'r', encoding='utf-8') as f:
                    example_content = f.read()
                
                # Check if already modified
                if "if sys.argv[1] == \"attributes\":" in example_content:
                    print("✅ Example script already modified")
                else:
                    # Look for existing command line handling
                    cli_pattern = r'if __name__ == "__main__" and len\(sys\.argv\) > 1:'
                    if cli_pattern in example_content:
                        # Replace existing handler
                        example_content = re.sub(
                            r'if __name__ == "__main__" and len\(sys\.argv\) > 1:.*?sys\.exit\(0\)',
                            EXAMPLE_SCRIPT_MODIFICATION,
                            example_content,
                            flags=re.DOTALL
                        )
                    else:
                        # Add new handler at the end
                        example_content += "\n\n" + EXAMPLE_SCRIPT_MODIFICATION
                    
                    # Write modified example script
                    with open(example_path, 'w', encoding='utf-8') as f:
                        f.write(example_content)
                    
                    print("✅ Modified example script to handle attribute manager")
            except Exception as e:
                print(f"⚠️ Warning: Could not modify example script: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error patching file: {e}")
        return False

def main():
    """Main function"""
    print("=== Replacing Existing Variant UI ===")
    
    # Confirm before proceeding
    confirm = input("This will replace the existing variant UI in add_product_dialog.py. Continue? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Create backup
    if not backup_file():
        print("❌ Failed to create backup. Aborting.")
        return
    
    # Patch file
    if patch_file():
        print("\n=== Replacement Complete! ===")
        print("The existing variant UI has been replaced with the new variant system.")
        print("You can now use the new variant system directly from the product add dialog.")
        print(f"\nIf you need to restore the original file, you can find a backup at: {BACKUP_PATH}")
    else:
        print("\n❌ Replacement failed.")
        print(f"You can restore from the backup at: {BACKUP_PATH}")

if __name__ == "__main__":
    main()
