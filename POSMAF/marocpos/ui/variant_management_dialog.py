from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QWidget, QSplitter, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QDialogButtonBox, QDoubleSpinBox, QSpinBox,
    QFormLayout, QGroupBox, QTabWidget, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from models.product_attribute import ProductAttribute
from models.product import Product
import json

class VariantManagementDialog(QDialog):
    def __init__(self, product_id=None, parent=None, variant_attributes=None):
        super().__init__(parent)
        self.product_id = product_id
        self.variant_attributes = variant_attributes or []  # List of attribute names
        self.attribute_values = {}  # Dict of attribute name -> list of values
        self.variants = []  # List of variant dictionaries
        self.existing_variants = []  # List of existing variants from the database
        self.init_ui()
        self.load_attributes()
        if self.product_id:
            self.load_existing_variants()

    def init_ui(self):
        self.setWindowTitle("Gestion des variantes de produit")
        self.setMinimumSize(900, 600)

        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_attributes_tab(), "1. Sélection des attributs")
        self.tabs.addTab(self.create_variants_tab(), "2. Variantes")
        
        main_layout.addWidget(self.tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def create_attributes_tab(self):
        """Create the attributes selection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instruction
        instruction = QLabel("Sélectionnez les attributs et valeurs à utiliser pour ce produit:")
        instruction.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(instruction)
        
        # Attribute selection layout
        self.attr_layout = QVBoxLayout()
        layout.addLayout(self.attr_layout)
        
        # Button to add another attribute
        add_attr_btn = QPushButton("Ajouter un attribut")
        add_attr_btn.clicked.connect(self.add_attribute_row)
        layout.addWidget(add_attr_btn)
        
        # Button to generate variants
        generate_btn = QPushButton("Générer les variantes")
        generate_btn.clicked.connect(self.generate_variants)
        layout.addWidget(generate_btn)
        
        # Manage attributes link
        manage_attr_btn = QPushButton("Gérer les attributs")
        manage_attr_btn.clicked.connect(self.open_attribute_management)
        layout.addWidget(manage_attr_btn)
        
        layout.addStretch()
        
        return tab

    def create_variants_tab(self):
        """Create the variants management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instruction
        instruction = QLabel("Gérez les variantes générées et leurs prix:")
        instruction.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(instruction)
        
        # Variants table
        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(7)  # Added one more column for actions
        self.variants_table.setHorizontalHeaderLabels([
            "Actif", "Variante", "SKU", "Prix de vente", "Stock", "Code-barres", "Actions"
        ])
        
        self.variants_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.variants_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.variants_table.setColumnWidth(0, 50)
        self.variants_table.setColumnWidth(6, 100)  # Actions column width
        
        # Enable context menu
        self.variants_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.variants_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.variants_table)
        
        # Bulk action buttons
        bulk_layout = QHBoxLayout()
        
        active_all_btn = QPushButton("Activer tout")
        active_all_btn.clicked.connect(lambda: self.set_all_active(True))
        
        deactive_all_btn = QPushButton("Désactiver tout")
        deactive_all_btn.clicked.connect(lambda: self.set_all_active(False))
        
        bulk_layout.addWidget(active_all_btn)
        bulk_layout.addWidget(deactive_all_btn)
        bulk_layout.addStretch()
        
        # Add buttons for editing operations
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.load_existing_variants)
        refresh_btn.setToolTip("Recharger les variantes depuis la base de données")
        
        save_btn = QPushButton("Enregistrer les modifications")
        save_btn.clicked.connect(self.save_variant_changes)
        save_btn.setToolTip("Sauvegarder les modifications sur les variantes existantes")
        
        bulk_layout.addWidget(refresh_btn)
        bulk_layout.addWidget(save_btn)
        
        layout.addLayout(bulk_layout)
        
        return tab
        
    def load_existing_variants(self):
        """Load existing variants from the database"""
        if not self.product_id:
            return
            
        try:
            # Clear existing variants in table
            self.variants_table.setRowCount(0)
            self.variants = []
            
            # Get variants from the database
            self.existing_variants = Product.get_variants(self.product_id)
            print(f"Loaded {len(self.existing_variants)} existing variants")
            
            if not self.existing_variants:
                # No existing variants, show a message
                return
                
            # Convert existing variants to our format and add to the variants list
            for variant in self.existing_variants:
                # Create a variant dict in our format
                formatted_variant = {
                    'id': variant.get('id'),
                    'active': True,
                    'name': variant.get('name', ''),
                    'sku': variant.get('sku', ''),
                    'price': float(variant.get('price_adjustment') or 0),
                    'stock': int(variant.get('stock') or 0),
                    'barcode': variant.get('barcode', ''),
                    'attributes': variant.get('attributes', {})
                }
                
                self.variants.append(formatted_variant)
            
            # Populate the table with the existing variants
            self.populate_variants_table()
            
            # Switch to the variants tab
            self.tabs.setCurrentIndex(1)
            
        except Exception as e:
            print(f"Error loading existing variants: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors du chargement des variantes existantes: {str(e)}"
            )
    
    def show_context_menu(self, position):
        """Show context menu for variant actions"""
        menu = QMenu()
        
        edit_action = menu.addAction("Modifier")
        delete_action = menu.addAction("Supprimer")
        
        # Get the item at the position
        item = self.variants_table.itemAt(position)
        if not item:
            return
            
        # Get the row of the item
        row = item.row()
        
        # Show the menu at the cursor position
        action = menu.exec_(QCursor.pos())
        
        # Handle the action
        if action == edit_action:
            self.edit_variant(row)
        elif action == delete_action:
            self.delete_variant(row)
            
    def edit_variant(self, row):
        """Edit a variant"""
        if row < 0 or row >= len(self.variants):
            return
            
        variant = self.variants[row]
        
        # Create a dialog to edit the variant
        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle(f"Modifier la variante: {variant['name']}")
        
        layout = QFormLayout(edit_dialog)
        
        # Create input fields
        name_input = QLineEdit(variant['name'])
        sku_input = QLineEdit(variant['sku'])
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0)
        price_input.setMaximum(999999.99)
        price_input.setValue(variant['price'])
        price_input.setSuffix(" MAD")
        stock_input = QSpinBox()
        stock_input.setMinimum(0)
        stock_input.setMaximum(999999)
        stock_input.setValue(variant['stock'])
        barcode_input = QLineEdit(variant['barcode'])
        
        # Add fields to layout
        layout.addRow("Nom:", name_input)
        layout.addRow("SKU:", sku_input)
        layout.addRow("Ajustement de prix:", price_input)
        layout.addRow("Stock:", stock_input)
        layout.addRow("Code-barres:", barcode_input)
        
        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(edit_dialog.accept)
        buttons.rejected.connect(edit_dialog.reject)
        layout.addRow(buttons)
        
        # Show the dialog
        if edit_dialog.exec_():
            # Update the variant with new values
            variant['name'] = name_input.text()
            variant['sku'] = sku_input.text()
            variant['price'] = price_input.value()
            variant['stock'] = stock_input.value()
            variant['barcode'] = barcode_input.text()
            
            # Update the table
            self.variants_table.item(row, 1).setText(variant['name'])
            self.variants_table.item(row, 2).setText(variant['sku'])
            price_spin = self.variants_table.cellWidget(row, 3)
            if price_spin:
                price_spin.setValue(variant['price'])
            stock_spin = self.variants_table.cellWidget(row, 4)
            if stock_spin:
                stock_spin.setValue(variant['stock'])
            self.variants_table.item(row, 5).setText(variant['barcode'])
    
    def delete_variant(self, row):
        """Delete a variant"""
        if row < 0 or row >= len(self.variants):
            return
            
        variant = self.variants[row]
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer la variante '{variant['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Check if it's an existing variant from database
        if 'id' in variant and variant['id']:
            # Delete from database
            if Product.delete_variant(variant['id']):
                # Remove from our lists
                self.variants.pop(row)
                self.variants_table.removeRow(row)
                QMessageBox.information(
                    self,
                    "Succès",
                    "Variante supprimée avec succès."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Erreur lors de la suppression de la variante."
                )
        else:
            # Just remove from our lists since it's not in database yet
            self.variants.pop(row)
            self.variants_table.removeRow(row)
    
    def save_variant_changes(self):
        """Save changes to existing variants"""
        success_count = 0
        error_count = 0
        
        for variant in self.variants:
            # Only process existing variants (ones with ID)
            if 'id' in variant and variant['id']:
                # Update variant in database
                # Use unit_price instead of price_adjustment based on the actual database structure
                update_data = {
                    'unit_price': variant['price'],  # Updated to use unit_price instead of price_adjustment
                    'stock': variant['stock'],
                    'barcode': variant['barcode'],
                    'name': variant['name'],
                    'sku': variant['sku'],
                    'attribute_values': variant['attributes']
                }
                
                # Print debug info
                print(f"Updating variant {variant['id']} with {update_data}")
                
                if Product.update_variant(variant['id'], **update_data):
                    success_count += 1
                else:
                    error_count += 1
        
        # Show result message
        if error_count == 0:
            QMessageBox.information(
                self,
                "Succès",
                f"{success_count} variantes mises à jour avec succès."
            )
        else:
            QMessageBox.warning(
                self,
                "Résultats",
                f"{success_count} variantes mises à jour avec succès. {error_count} erreurs."
            )

    def load_attributes(self):
        """Load existing attributes and generate UI"""
        # Clear existing
        self.clear_attribute_rows()
        
        # Add initial rows based on existing variant_attributes
        if self.variant_attributes:
            for attr_name in self.variant_attributes:
                self.add_attribute_row(attr_name)
        else:
            # Add at least one empty row
            self.add_attribute_row()

    def add_attribute_row(self, selected_attr=None):
        """Add a row for attribute selection"""
        # Get all attributes
        attributes = ProductAttribute.get_all_attributes()
        if not attributes:
            QMessageBox.warning(
                self, 
                "Aucun attribut", 
                "Vous devez créer des attributs d'abord. Utilisez le bouton 'Gérer les attributs'"
            )
            return
            
        # Create the row widget
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Attribute dropdown
        attr_combo = QComboBox()
        for attr in attributes:
            attr_combo.addItem(attr['name'], attr['id'])
            
        # Set selected attribute if provided
        if selected_attr:
            for i in range(attr_combo.count()):
                if attr_combo.itemText(i) == selected_attr:
                    attr_combo.setCurrentIndex(i)
                    break
        
        # Values checkboxes container
        values_widget = QWidget()
        self.values_layout = QHBoxLayout(values_widget)
        self.values_layout.setContentsMargins(0, 0, 0, 0)
        
        # Connect attribute change to value refresh
        attr_combo.currentIndexChanged.connect(
            lambda: self.refresh_values(values_widget, attr_combo.currentText())
        )
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.remove_attribute_row(row_widget))
        
        # Add widgets to row
        row_layout.addWidget(QLabel("Attribut:"))
        row_layout.addWidget(attr_combo)
        row_layout.addWidget(QLabel("Valeurs:"))
        row_layout.addWidget(values_widget, 1)  # 1 = stretch factor
        row_layout.addWidget(delete_btn)
        
        # Add row to layout
        self.attr_layout.addWidget(row_widget)
        
        # Initialize values
        self.refresh_values(values_widget, attr_combo.currentText())

    def refresh_values(self, container, attribute_name):
        """Refresh the values checkboxes for an attribute"""
        # Clear the container
        while container.layout().count():
            item = container.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Skip if no attribute is selected
        if not attribute_name:
            return
            
        # Get attribute values
        values = []
        attributes = ProductAttribute.get_all_attributes()
        for attr in attributes:
            if attr.get('name') == attribute_name:
                try:
                    values = ProductAttribute.get_attribute_values(attr['id'])
                except Exception as e:
                    print(f"Error getting attribute values: {e}")
                break
        
        # Add checkboxes for each value
        for value in values:
            cb = QCheckBox(value['value'])
            cb.setChecked(True)  # Default to checked
            container.layout().addWidget(cb)
        
        # Add a spacer at the end
        container.layout().addStretch()

    def remove_attribute_row(self, row_widget):
        """Remove an attribute row"""
        self.attr_layout.removeWidget(row_widget)
        row_widget.deleteLater()

    def clear_attribute_rows(self):
        """Clear all attribute rows"""
        while self.attr_layout.count():
            item = self.attr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def collect_attribute_values(self):
        """Collect the selected attributes and their values"""
        self.attribute_values = {}
        
        # Iterate through attribute rows
        for i in range(self.attr_layout.count()):
            widget = self.attr_layout.itemAt(i).widget()
            if not widget:
                continue
                
            # Get the attribute dropdown
            attr_combo = None
            values_widget = None
            
            for j in range(widget.layout().count()):
                item = widget.layout().itemAt(j).widget()
                if isinstance(item, QComboBox):
                    attr_combo = item
                elif isinstance(item, QWidget) and item.layout() and item.layout().count() > 0:
                    values_widget = item
            
            if not attr_combo or not values_widget:
                continue
                
            # Check if an attribute is actually selected
            if attr_combo.currentIndex() < 0:
                continue
                
            # Get the attribute name
            attr_name = attr_combo.currentText()
            
            # Skip empty attribute names
            if not attr_name.strip():
                continue
            
            # Get selected values
            selected_values = []
            for j in range(values_widget.layout().count()):
                item = values_widget.layout().itemAt(j).widget()
                if isinstance(item, QCheckBox) and item.isChecked():
                    selected_values.append(item.text())
            
            # Add to our dictionary
            if selected_values:
                self.attribute_values[attr_name] = selected_values
        
        # Debug output to help diagnose issues
        print(f"Collected attribute values: {self.attribute_values}")
        
        return self.attribute_values

    def generate_variants(self):
        """Generate variants based on selected attributes and values"""
        # Collect attribute values
        attr_values = self.collect_attribute_values()
        
        if not attr_values:
            QMessageBox.warning(self, "Aucune variante", "Aucun attribut ou valeur sélectionné.")
            return
            
        # Generate combinations with the dict approach
        combinations = ProductAttribute.generate_variant_combinations_dict(attr_values)
        
        # Store as list of variant dictionaries
        self.variants = []
        for combo in combinations:
            # Create variant name from combination (e.g., "Red / L")
            name_parts = []
            for attr, value in combo.items():
                name_parts.append(f"{value}")
            
            variant_name = " / ".join(name_parts)
            
            # Generate a more unique SKU
            base_sku = "SKU"  # This would normally come from the product
            sku_parts = []
            
            # Get first 2 letters (or full word if shorter) of each value, with attribute first letter
            for attr, value in combo.items():
                # Clean and normalize the value - remove spaces and special characters
                cleaned_value = ''.join(c for c in value if c.isalnum())
                # Get attribute first letter + up to 2 chars from value
                attr_prefix = attr[0].upper()
                value_part = cleaned_value[:2].upper()
                sku_parts.append(f"{attr_prefix}{value_part}")
            
            # Add a unique timestamp-based suffix to ensure uniqueness
            import time
            timestamp_suffix = str(int(time.time() * 1000))[-4:]  # Last 4 digits of current time in ms
            
            sku = f"{base_sku}-{''.join(sku_parts)}-{timestamp_suffix}"
            
            # Create variant dictionary
            variant = {
                'active': True,
                'name': variant_name,
                'sku': sku,
                'price': 0.0,  # Default price from product
                'stock': 0,
                'barcode': '',
                'attributes': combo
            }
            
            self.variants.append(variant)
        
        # Populate the variants table
        self.populate_variants_table()

    def populate_variants_table(self):
        """Populate the variants table with generated variants"""
        self.variants_table.setRowCount(len(self.variants))
        
        for row, variant in enumerate(self.variants):
            # Active checkbox
            active_cb = QCheckBox()
            active_cb.setChecked(variant['active'])
            active_cb.stateChanged.connect(lambda state, r=row: self.update_variant_active(r, state))
            active_cell = QWidget()
            active_layout = QHBoxLayout(active_cell)
            active_layout.addWidget(active_cb)
            active_layout.setAlignment(Qt.AlignCenter)
            active_layout.setContentsMargins(0, 0, 0, 0)
            
            # Variant name
            name_item = QTableWidgetItem(variant['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            # Store variant ID in the name item if it exists
            if 'id' in variant and variant['id']:
                name_item.setData(Qt.UserRole, variant['id'])
                # Add a visual indicator for existing variants
                name_item.setToolTip(f"ID: {variant['id']} (Variante existante)")
            
            # SKU
            sku_item = QTableWidgetItem(variant['sku'])
            
            # Price widget
            price_spin = QDoubleSpinBox()
            price_spin.setMinimum(0)
            price_spin.setMaximum(999999.99)
            price_spin.setValue(variant['price'])
            price_spin.setSuffix(" MAD")
            price_spin.valueChanged.connect(lambda value, r=row: self.update_variant_price(r, value))
            
            # Stock widget
            stock_spin = QSpinBox()
            stock_spin.setMinimum(0)
            stock_spin.setMaximum(999999)
            stock_spin.setValue(variant['stock'])
            stock_spin.valueChanged.connect(lambda value, r=row: self.update_variant_stock(r, value))
            
            # Barcode
            barcode_item = QTableWidgetItem(variant['barcode'])
            barcode_item.setData(Qt.UserRole, variant)
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            
            # Edit button
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier cette variante")
            edit_btn.setFixedSize(30, 25)
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_variant(r))
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Supprimer cette variante")
            delete_btn.setFixedSize(30, 25)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_variant(r))
            
            # Add buttons to actions layout
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            # Add to table
            self.variants_table.setCellWidget(row, 0, active_cell)
            self.variants_table.setItem(row, 1, name_item)
            self.variants_table.setItem(row, 2, sku_item)
            self.variants_table.setCellWidget(row, 3, price_spin)
            self.variants_table.setCellWidget(row, 4, stock_spin)
            self.variants_table.setItem(row, 5, barcode_item)
            self.variants_table.setCellWidget(row, 6, actions_widget)

    def update_variant_active(self, row, state):
        """Update the active state of a variant"""
        if row < len(self.variants):
            self.variants[row]['active'] = (state == Qt.Checked)

    def update_variant_price(self, row, value):
        """Update the price of a variant"""
        if row < len(self.variants):
            self.variants[row]['price'] = value

    def update_variant_stock(self, row, value):
        """Update the stock of a variant"""
        if row < len(self.variants):
            self.variants[row]['stock'] = value

    def set_all_active(self, active):
        """Set all variants active or inactive"""
        for row in range(self.variants_table.rowCount()):
            cell_widget = self.variants_table.cellWidget(row, 0)
            if cell_widget:
                # Find the checkbox in the cell widget
                for i in range(cell_widget.layout().count()):
                    checkbox = cell_widget.layout().itemAt(i).widget()
                    if isinstance(checkbox, QCheckBox):
                        checkbox.setChecked(active)
                        break

    def open_attribute_management(self):
        """Open the attribute management dialog"""
        # Import on-demand to avoid circular dependencies
        try:
            module = __import__('ui.attribute_management_dialog', fromlist=['AttributeManagementDialog'])
            AttributeManagementDialog = module.AttributeManagementDialog
            
            dialog = AttributeManagementDialog(self)
            if dialog.exec_():
                # Refresh our attribute list
                self.load_attributes()
        except ImportError:
            QMessageBox.warning(
                self,
                "Module manquant",
                "Le module de gestion des attributs n'est pas disponible. Veuillez vérifier votre installation."
            )
        except Exception as e:
            print(f"Error opening attribute management: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                f"Une erreur s'est produite lors de l'ouverture de la gestion des attributs: {str(e)}"
            )

    def get_variants_data(self):
        """Get the configured variants data"""
        result = []
        
        # Update SKUs and barcodes from the table
        for row in range(self.variants_table.rowCount()):
            variant = self.variants[row]
            sku_item = self.variants_table.item(row, 2)
            barcode_item = self.variants_table.item(row, 5)
            
            if sku_item:
                variant['sku'] = sku_item.text()
            if barcode_item:
                variant['barcode'] = barcode_item.text()
            
            # Add only active variants
            if variant['active']:
                # Convert attribute dict to string format
                variant_data = {
                    'name': variant['name'],
                    'sku': variant['sku'],
                    'barcode': variant['barcode'],
                    'price': variant['price'],
                    'stock': variant['stock'],
                    'attribute_values': json.dumps(variant['attributes'])
                }
                result.append(variant_data)
        
        return result

    def get_attribute_names(self):
        """Get the names of attributes used"""
        return list(self.attribute_values.keys())
