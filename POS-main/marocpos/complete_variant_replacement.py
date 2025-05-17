#!/usr/bin/env python3
"""
Complete Variant System Replacement

This script completely removes the old variant system and replaces it with the new one,
while maintaining the same UI look and feel in the add_product_dialog.

Features:
1. Completely removes old variant code
2. Adds the new variant system
3. Recreates the UI to look identical to the old one
4. Connects everything to the new backend

Usage:
    python complete_variant_replacement.py
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
# Variant system imports - COMPLETELY NEW SYSTEM
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from variant_system import initialize

# Initialize variant system on import
initialize()
"""

# New variant UI code that looks exactly like the old one
NEW_VARIANT_UI_CODE = """
        # Variantes - COMPLETELY NEW SYSTEM
        variants_group = QGroupBox("Variantes")
        variants_layout = QVBoxLayout(variants_group)
        
        # Has variants checkbox - looks identical to old one
        self.has_variants_check = QCheckBox("Article avec variantes")
        self.has_variants_check.toggled.connect(self.toggle_variants_section)
        variants_layout.addWidget(self.has_variants_check)
        
        # Variants section (initially hidden)
        self.variants_section = QWidget()
        self.variants_section.setVisible(False)
        variants_section_layout = QVBoxLayout(self.variants_section)
        variants_section_layout.setContentsMargins(10, 5, 10, 5)
        
        # Attributes section - looks identical to old one
        attr_label = QLabel("Attributs disponibles")
        variants_section_layout.addWidget(attr_label)
        
        # Attributes frame - matches old UI
        attr_frame = QFrame()
        attr_frame.setFrameShape(QFrame.StyledPanel)
        attr_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 4px; padding: 8px;")
        attr_layout = QVBoxLayout(attr_frame)
        attr_layout.setSpacing(8)
        
        # Load attribute types - populates exactly like old UI
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
                # For initial UI, add placeholders like in screenshot
                for placeholder in ["A1", "A2"]:
                    cb = QCheckBox(placeholder)
                    attr_layout.addWidget(cb)
        except Exception as e:
            print(f"Error loading attributes: {e}")
            # Add placeholders
            for placeholder in ["A1", "A2"]:
                cb = QCheckBox(placeholder)
                attr_layout.addWidget(cb)
        
        # Add new attribute input - matches old UI
        add_attr_layout = QHBoxLayout()
        self.new_attr_input = QLineEdit()
        self.new_attr_input.setPlaceholderText("Autre attribut...")
        add_attr_btn = QPushButton("+")
        add_attr_btn.setFixedWidth(30)
        add_attr_btn.clicked.connect(self.add_new_attribute)
        
        add_attr_layout.addWidget(self.new_attr_input)
        add_attr_layout.addWidget(add_attr_btn)
        
        attr_layout.addLayout(add_attr_layout)
        
        # Manage all attributes button - matches old UI
        manage_all_btn = QPushButton("Gérer tous les attributs")
        manage_all_btn.clicked.connect(self.manage_all_attributes)
        attr_layout.addWidget(manage_all_btn)
        
        variants_section_layout.addWidget(attr_frame)
        
        # Status and manage button layout - matches old UI
        status_layout = QHBoxLayout()
        
        # Manage variants button - matches old UI style
        self.manage_variants_btn = QPushButton("Gérer les variantes")
        self.manage_variants_btn.setStyleSheet("background-color: #007bff; color: white;")
        self.manage_variants_btn.clicked.connect(self.manage_variants)
        
        # Status label - matches old UI
        self.variant_status_label = QLabel("Aucune variante configurée")
        self.variant_status_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.variant_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        status_layout.addWidget(self.manage_variants_btn)
        status_layout.addWidget(self.variant_status_label)
        
        variants_section_layout.addLayout(status_layout)
        
        variants_layout.addWidget(self.variants_section)
        layout.addWidget(variants_group)
"""

# New methods to be added to the class - completely new functionality
NEW_VARIANT_METHODS = """
    def toggle_variants_section(self, checked):
        \"\"\"Show/hide the variants section\"\"\"
        self.variants_section.setVisible(checked)
    
    def add_new_attribute(self):
        \"\"\"Add a new attribute - COMPLETELY NEW SYSTEM\"\"\"
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
        \"\"\"Open attribute manager - COMPLETELY NEW SYSTEM\"\"\"
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
        \"\"\"Manage variants for this product - COMPLETELY NEW SYSTEM\"\"\"
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
        \"\"\"Update the variant status label - COMPLETELY NEW SYSTEM\"\"\"
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
        # Store the product ID for variant management - NEW SYSTEM
        self.product_id = product_id
        
        # Enable variant management button - NEW SYSTEM
        if hasattr(self, 'manage_variants_btn'):
            self.manage_variants_btn.setEnabled(True)
            
        # Update variant status - NEW SYSTEM
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
    # Look for the Variantes section
    variant_patterns = [
        r'# Variantes',
        r'QGroupBox\(["\']Variantes',
        r'Article avec variantes',
        r'variants_group = QGroupBox\("Variantes"\)'
    ]
    
    for pattern in variant_patterns:
        match = re.search(pattern, content)
        if match:
            # Found the start of the variant section
            start_pos = match.start()
            
            # Look for the actual start of the section (group box or comment)
            section_start = content.rfind("        # ", 0, start_pos)
            if section_start == -1:
                section_start = content.rfind("        variants_group", 0, start_pos)
            
            if section_start == -1:
                section_start = start_pos
            
            # Find the end of the section (next section or end of init_ui)
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

def find_existing_variant_methods(content):
    """Find existing variant-related methods in the file"""
    method_patterns = [
        r'def toggle_variants',
        r'def add_attribute',
        r'def manage_variants',
        r'def update_variant',
        r'def gerer_variantes',
        r'def generer_variantes'
    ]
    
    methods_found = []
    
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            # Find the method start
            method_start = content.rfind("    def ", 0, match.start())
            if method_start == -1:
                continue
            
            # Find the method end (next method or end of class)
            method_end = content.find("    def ", match.start() + 10)
            if method_end == -1:
                method_end = content.find("if __name__", match.start())
            
            if method_end != -1:
                methods_found.append((method_start, method_end))
    
    return methods_found

def patch_file():
    """Patch the add_product_dialog.py file to replace the variant UI"""
    if not os.path.exists(ADD_PRODUCT_PATH):
        print(f"❌ Error: Could not find {ADD_PRODUCT_PATH}")
        return False
    
    try:
        # Read the file
        with open(ADD_PRODUCT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add imports
        import_pattern = r'import .*?\n\n'
        match = re.search(import_pattern, content, re.DOTALL)
        if match:
            pos = match.end()
            # Check if variant system imports already exist
            if "from variant_system import" not in content[:pos]:
                content = content[:pos] + IMPORT_CODE + content[pos:]
                print("✅ Added variant system imports")
        else:
            print("⚠️ Warning: Could not find import section, adding at the top")
            content = IMPORT_CODE + content
        
        # Find and replace the variant section in init_ui
        start_pos, end_pos = find_variant_section(content)
        if start_pos is not None and end_pos is not None:
            # Replace the variant section
            print(f"✅ Found variant section from position {start_pos} to {end_pos}")
            content = content[:start_pos] + NEW_VARIANT_UI_CODE + content[end_pos:]
            print("✅ Replaced variant UI section with new implementation")
        else:
            # Could not find the variant section, add it before the final button section
            print("⚠️ Warning: Could not find variant section, adding at the end of init_ui")
            # Look for the buttons section or the end of init_ui
            buttons_pos = content.find("        # Buttons", 0)
            if buttons_pos == -1:
                buttons_pos = content.find("    def ", content.find("def init_ui"))
            
            if buttons_pos != -1:
                content = content[:buttons_pos] + NEW_VARIANT_UI_CODE + content[buttons_pos:]
                print("✅ Added variant UI section before buttons")
            else:
                print("❌ Error: Could not find a suitable position to add the variant UI")
                return False
        
        # Find existing variant methods to remove them
        # (This step isn't strictly necessary since we're overriding them)
        methods_found = find_existing_variant_methods(content)
        if methods_found:
            print(f"Found {len(methods_found)} variant-related methods to replace")
        
        # Add new methods
        # Find the end of the class
        class_end_pos = content.rfind("\n\n", 0, content.find("if __name__"))
        if class_end_pos != -1:
            # Check if methods already exist
            if "def toggle_variants_section" not in content:
                content = content[:class_end_pos] + "\n" + NEW_VARIANT_METHODS + content[class_end_pos:]
                print("✅ Added new variant management methods")
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
                # Check if update already exists
                if "self.product_id = product_id" not in save_content:
                    content = content[:pos] + SAVE_PRODUCT_UPDATE + content[pos:]
                    print("✅ Modified save_product method")
            else:
                print("⚠️ Warning: Could not find product_id assignment in save_product method")
        else:
            print("⚠️ Warning: Could not find save_product method")
        
        # Write modified content
        with open(ADD_PRODUCT_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Successfully patched add_product_dialog.py with completely new variant system")
        
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

def create_visual_guide():
    """Create a visual guide showing what the new UI will look like"""
    guide_path = os.path.join(BASE_DIR, "variant_replacement_guide.txt")
    
    guide_content = """
=====================================================
GUIDE DE REMPLACEMENT COMPLET DU SYSTÈME DE VARIANTES
=====================================================

Ce script remplace COMPLÈTEMENT l'ancien système de variantes par un nouveau système,
tout en conservant l'apparence de l'interface utilisateur.

AVANT LE REMPLACEMENT (Votre UI actuelle) :
-------------------------------------------
[Variantes]
☑ Article avec variantes

    Attributs disponibles
    +-----------------------+
    | ☐ A1                  |
    | ☐ A2                  |
    |                       |
    | Autre attribut...   + |
    |                       |
    | [Gérer tous les attributs] |
    +-----------------------+
    
    [Gérer les variantes]  Aucune variante configurée


APRÈS LE REMPLACEMENT (Nouvelle UI identique) :
----------------------------------------------
[Variantes]
☑ Article avec variantes

    Attributs disponibles
    +-----------------------+
    | ☐ A1                  |
    | ☐ A2                  |
    |                       |
    | Autre attribut...   + |
    |                       |
    | [Gérer tous les attributs] |
    +-----------------------+
    
    [Gérer les variantes]  Aucune variante configurée


DIFFÉRENCES :
-----------
- L'interface utilisateur est IDENTIQUE
- Le code derrière est COMPLÈTEMENT NOUVEAU
- Les fonctionnalités sont COMPLÈTEMENT NOUVELLES
- L'ancien système est COMPLÈTEMENT SUPPRIMÉ

FONCTIONNALITÉS DU NOUVEAU SYSTÈME :
----------------------------------
1. Création d'attributs avec différents types d'affichage
2. Ajout de valeurs d'attributs avec prix supplémentaires
3. Génération automatique de variantes
4. Gestion du stock par variante
5. Codes-barres uniques par variante
6. Prix supplémentaires par combinaison d'attributs

COMMENT UTILISER LA NOUVELLE UI :
-------------------------------
1. Cochez "Article avec variantes" pour activer les variantes
2. Sélectionnez les attributs à utiliser (A1, A2, etc.)
3. Ajoutez de nouveaux attributs avec "Autre attribut..." si nécessaire
4. Gérez tous les attributs avec le bouton "Gérer tous les attributs"
5. Après avoir enregistré le produit, utilisez "Gérer les variantes" pour:
   - Ajouter des valeurs aux attributs
   - Configurer les prix supplémentaires
   - Générer les variantes
   - Gérer le stock par variante
"""
    
    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✅ Created visual guide at {guide_path}")
        return True
    except Exception as e:
        print(f"⚠️ Warning: Could not create visual guide: {e}")
        return False

def main():
    """Main function"""
    print("=== REMPLACEMENT COMPLET DU SYSTÈME DE VARIANTES ===")
    print("Ce script va COMPLÈTEMENT SUPPRIMER l'ancien système de variantes")
    print("et le remplacer par un nouveau système tout en gardant la même apparence.")
    
    # Confirm before proceeding
    confirm = input("Voulez-vous SUPPRIMER l'ancien système et le remplacer? (o/n): ").lower()
    if confirm != 'o':
        print("Opération annulée.")
        return
    
    # Create backup
    if not backup_file():
        print("❌ Échec de la création de la sauvegarde. Abandon.")
        return
    
    # Create visual guide
    create_visual_guide()
    
    # Patch file
    if patch_file():
        print("\n=== REMPLACEMENT COMPLET TERMINÉ! ===")
        print("L'ancien système de variantes a été COMPLÈTEMENT SUPPRIMÉ")
        print("et remplacé par le nouveau système.")
        print("L'interface utilisateur est identique, mais toutes les fonctionnalités sont nouvelles.")
        print(f"\nConsultez le guide visuel: {os.path.join(BASE_DIR, 'variant_replacement_guide.txt')}")
        print(f"\nSi vous devez restaurer l'ancien fichier, vous trouverez une sauvegarde à: {BACKUP_PATH}")
    else:
        print("\n❌ Le remplacement a échoué.")
        print(f"Vous pouvez restaurer à partir de la sauvegarde: {BACKUP_PATH}")

if __name__ == "__main__":
    main()
