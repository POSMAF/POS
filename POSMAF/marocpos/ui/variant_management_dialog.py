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
        """Edit a variant with business rule validation"""
        if row < 0 or row >= len(self.variants):
            return
            
        variant = self.variants[row]
        
        # Get product information for margin calculation
        product_info = None
        if self.product_id:
            product_info = self.get_product_info(self.product_id)
            
        # Create a dialog to edit the variant
        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle(f"Modifier la variante: {variant['name']}")
        edit_dialog.setMinimumWidth(500)
        
        layout = QFormLayout(edit_dialog)
        
        # Create input fields
        name_input = QLineEdit(variant['name'])
        sku_input = QLineEdit(variant['sku'])
        
        # Price input with margin calculation
        price_frame = QFrame()
        price_layout = QVBoxLayout(price_frame)
        price_layout.setContentsMargins(0, 0, 0, 0)
        
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0)
        price_input.setMaximum(999999.99)
        price_input.setValue(variant['price'])
        price_input.setSuffix(" MAD")
        price_layout.addWidget(price_input)
        
        # Add purchase price and margin information
        purchase_price = 0
        if product_info and 'purchase_price' in product_info:
            purchase_price = float(product_info['purchase_price'] or 0)
            
            # Create margin display label
            self.margin_label = QLabel()
            self.margin_label.setStyleSheet("font-size: 11px;")
            price_layout.addWidget(self.margin_label)
            
            # Function to update margin calculation
            def update_margin_display():
                selling_price = price_input.value()
                margin = selling_price - purchase_price
                margin_percent = (margin / purchase_price * 100) if purchase_price > 0 else 0
                
                if margin < 0:
                    self.margin_label.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
                    self.margin_label.setText(f"ALERTE: Marge négative! {margin:.2f} MAD ({margin_percent:.1f}%)")
                elif margin_percent < 10:
                    self.margin_label.setStyleSheet("color: orange; font-size: 11px;")
                    self.margin_label.setText(f"Marge faible: {margin:.2f} MAD ({margin_percent:.1f}%)")
                else:
                    self.margin_label.setStyleSheet("color: green; font-size: 11px;")
                    self.margin_label.setText(f"Marge: {margin:.2f} MAD ({margin_percent:.1f}%)")
            
            # Connect price changes to margin updates
            price_input.valueChanged.connect(update_margin_display)
            
            # Initial update
            update_margin_display()
            
            # Add purchase price info
            purchase_info = QLabel(f"Prix d'achat: {purchase_price:.2f} MAD")
            purchase_info.setStyleSheet("font-size: 11px; color: #666;")
            price_layout.addWidget(purchase_info)
        
        stock_input = QSpinBox()
        stock_input.setMinimum(0)
        stock_input.setMaximum(999999)
        stock_input.setValue(variant['stock'])
        barcode_input = QLineEdit(variant['barcode'])
        
        # Check if variant attributes are empty and warn
        has_attributes = variant.get('attributes') and len(variant.get('attributes', {})) > 0
        
        # Add attribute warning if needed
        if not has_attributes:
            attr_warning = QLabel("⚠️ Cette variante n'a pas d'attributs définis!")
            attr_warning.setStyleSheet("color: red; font-weight: bold;")
            layout.addRow(attr_warning)
        
        # Add fields to layout
        layout.addRow("Nom:", name_input)
        layout.addRow("SKU:", sku_input)
        layout.addRow("Prix de vente:", price_frame)
        layout.addRow("Stock:", stock_input)
        layout.addRow("Code-barres:", barcode_input)
        
        # Business rules section
        rules_frame = QFrame()
        rules_frame.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        rules_layout = QVBoxLayout(rules_frame)
        
        rules_title = QLabel("Règles commerciales")
        rules_title.setStyleSheet("font-weight: bold;")
        rules_layout.addWidget(rules_title)
        
        # Add business rule checkboxes
        prevent_negative_margin = QCheckBox("Empêcher les marges négatives")
        prevent_negative_margin.setChecked(True)
        rules_layout.addWidget(prevent_negative_margin)
        
        layout.addRow(rules_frame)
        
        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.validate_and_accept_variant_edit(
            edit_dialog, 
            variant, 
            name_input.text(),
            sku_input.text(),
            price_input.value(),
            stock_input.value(),
            barcode_input.text(),
            purchase_price,
            prevent_negative_margin.isChecked(),
            has_attributes
        ))
        buttons.rejected.connect(edit_dialog.reject)
        layout.addRow(buttons)
        
        # Show the dialog
        edit_dialog.exec_()
    
    def validate_and_accept_variant_edit(self, dialog, variant, name, sku, price, stock, barcode, 
                                          purchase_price, prevent_negative_margin, has_attributes):
        """Validate variant data against business rules before accepting"""
        validation_errors = []
        
        # Check for empty name
        if not name.strip():
            validation_errors.append("Le nom de la variante ne peut pas être vide")
            
        # Check for empty SKU
        if not sku.strip():
            validation_errors.append("Le SKU ne peut pas être vide")
            
        # Check for negative margin if enabled
        if prevent_negative_margin and purchase_price > 0 and price < purchase_price:
            margin = price - purchase_price
            validation_errors.append(f"Prix de vente ({price:.2f} MAD) inférieur au prix d'achat ({purchase_price:.2f} MAD). Marge: {margin:.2f} MAD")
            
        # Check for excessively large price reduction from base price
        if self.product_id:
            product_info = self.get_product_info(self.product_id)
            if product_info and 'unit_price' in product_info:
                base_price = float(product_info['unit_price'] or 0)
                if price < base_price * 0.5:  # More than 50% reduction
                    validation_errors.append(f"Réduction excessive: {price:.2f} MAD est plus de 50% inférieur au prix de base ({base_price:.2f} MAD)")
        
        # Enforce attributes if the variant doesn't have any
        if not has_attributes:
            # Just warn, don't prevent saving
            QMessageBox.warning(
                dialog,
                "Avertissement",
                "Cette variante n'a pas d'attributs définis. Il est recommandé d'ajouter des attributs pour une meilleure organisation."
            )
        
        # Show validation errors if any
        if validation_errors:
            error_message = "Veuillez corriger les erreurs suivantes:\n\n" + "\n".join(f"• {error}" for error in validation_errors)
            QMessageBox.warning(dialog, "Validation échouée", error_message)
            return
        
        # If everything is valid, update the variant
        variant['name'] = name
        variant['sku'] = sku
        variant['price'] = price
        variant['stock'] = stock
        variant['barcode'] = barcode
        
        # Update the table
        row = self.variants.index(variant)
        self.variants_table.item(row, 1).setText(variant['name'])
        self.variants_table.item(row, 2).setText(variant['sku'])
        price_spin = self.variants_table.cellWidget(row, 3)
        if price_spin:
            price_spin.setValue(variant['price'])
        stock_spin = self.variants_table.cellWidget(row, 4)
        if stock_spin:
            stock_spin.setValue(variant['stock'])
        self.variants_table.item(row, 5).setText(variant['barcode'])
        
        # Close the dialog
        dialog.accept()
        
    def get_product_info(self, product_id):
        """Get product information for margin calculation"""
        try:
            from models.product import Product
            return Product.get_product(product_id)
        except Exception as e:
            print(f"Error getting product info: {e}")
            return None
    
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
            
        # Get product info for default pricing and business rules
        product_info = None
        base_price = 0
        purchase_price = 0
        
        if self.product_id:
            product_info = self.get_product_info(self.product_id)
            if product_info:
                base_price = float(product_info.get('unit_price', 0) or 0)
                purchase_price = float(product_info.get('purchase_price', 0) or 0)
        
        # Calculate default minimum price (ensures a 15% margin)
        min_price = purchase_price * 1.15 if purchase_price > 0 else base_price
        default_price = max(base_price, min_price)
        
        # Ask user about pricing strategy
        if base_price > 0:
            strategy_msg = QMessageBox(self)
            strategy_msg.setWindowTitle("Stratégie de tarification des variantes")
            strategy_msg.setText("Comment souhaitez-vous tarifer les nouvelles variantes?")
            strategy_msg.setIcon(QMessageBox.Question)
            
            # Add pricing options
            base_btn = strategy_msg.addButton(f"Prix de base ({base_price:.2f} MAD)", QMessageBox.AcceptRole)
            safe_btn = strategy_msg.addButton(f"Prix sécurisé ({default_price:.2f} MAD)", QMessageBox.AcceptRole)
            custom_btn = strategy_msg.addButton("Prix personnalisé", QMessageBox.AcceptRole)
            cancel_btn = strategy_msg.addButton(QMessageBox.Cancel)
            
            # Show dialog and get result
            strategy_msg.exec_()
            
            # Process result
            if strategy_msg.clickedButton() == cancel_btn:
                return
            elif strategy_msg.clickedButton() == custom_btn:
                # Get custom price
                from PyQt5.QtWidgets import QInputDialog
                custom_price, ok = QInputDialog.getDouble(
                    self, 
                    "Prix personnalisé", 
                    f"Entrez le prix pour toutes les variantes (min. recommandé: {min_price:.2f}):", 
                    base_price, min_price, 999999.99, 2
                )
                if not ok:
                    return
                default_price = custom_price
            elif strategy_msg.clickedButton() == safe_btn:
                default_price = min_price
            else:  # base_btn
                default_price = base_price
            
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
            if product_info and product_info.get('name'):
                # Use first 3 chars of product name if available
                prod_name = ''.join(c for c in product_info['name'] if c.isalnum())
                base_sku = prod_name[:3].upper()
                
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
                'price': default_price,  # Use safe default price
                'stock': 0,
                'barcode': '',
                'attributes': combo
            }
            
            # If we have purchase price info, add it to the variant for margin calculations
            if purchase_price > 0:
                variant['purchase_price'] = purchase_price
            
            self.variants.append(variant)
            
        # Show confirmation message
        QMessageBox.information(
            self,
            "Variantes générées",
            f"{len(self.variants)} variantes ont été générées avec le prix de {default_price:.2f} MAD.\n\n"
            f"Vous pouvez maintenant modifier les prix individuellement si nécessaire."
        )
        
        # Populate the variants table
        self.populate_variants_table()

    def populate_variants_table(self):
        """Populate the variants table with generated variants"""
        self.variants_table.setRowCount(len(self.variants))
        
        # Get product info for margin calculations
        product_info = None
        if self.product_id:
            product_info = self.get_product_info(self.product_id)
            
        # Get purchase price for margin calculation
        purchase_price = 0
        base_price = 0
        if product_info:
            purchase_price = float(product_info.get('purchase_price', 0) or 0)
            base_price = float(product_info.get('unit_price', 0) or 0)
        
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
            
            # Check if variant has empty attributes and add warning indicator
            has_attributes = variant.get('attributes') and len(variant.get('attributes', {})) > 0
            if not has_attributes:
                name_item.setText(f"⚠️ {variant['name']}")
                name_item.setToolTip("Attention: Cette variante n'a pas d'attributs définis!")
                name_item.setForeground(Qt.red)
            
            # Store variant ID in the name item if it exists
            if 'id' in variant and variant['id']:
                name_item.setData(Qt.UserRole, variant['id'])
                # Add a visual indicator for existing variants
                name_item.setToolTip(f"ID: {variant['id']} (Variante existante)")
            
            # SKU
            sku_item = QTableWidgetItem(variant['sku'])
            
            # Price widget with margin validation
            price_widget = QWidget()
            price_layout = QVBoxLayout(price_widget)
            price_layout.setContentsMargins(0, 0, 0, 0)
            price_layout.setSpacing(0)
            
            price_spin = QDoubleSpinBox()
            price_spin.setMinimum(0)
            price_spin.setMaximum(999999.99)
            price_spin.setValue(variant['price'])
            price_spin.setSuffix(" MAD")
            
            # Calculate margin and add visual indicators
            if purchase_price > 0:
                margin = variant['price'] - purchase_price
                margin_percent = (margin / purchase_price * 100) if purchase_price > 0 else 0
                
                # Style the price spinbox based on margin
                if margin < 0:
                    price_spin.setStyleSheet("QDoubleSpinBox { background-color: #ffcccc; color: red; font-weight: bold; }")
                    tooltip = f"ALERTE: Marge négative! {margin:.2f} MAD ({margin_percent:.1f}%)"
                elif margin_percent < 10:
                    price_spin.setStyleSheet("QDoubleSpinBox { background-color: #fff3cd; }")
                    tooltip = f"Marge faible: {margin:.2f} MAD ({margin_percent:.1f}%)"
                else:
                    tooltip = f"Marge: {margin:.2f} MAD ({margin_percent:.1f}%)"
                
                price_spin.setToolTip(tooltip)
                
                # Add margin indicator label for negative margins
                if margin < 0:
                    margin_indicator = QLabel(f"⚠️ -{abs(margin):.0f} MAD")
                    margin_indicator.setStyleSheet("color: red; font-size: 9px;")
                    price_layout.addWidget(margin_indicator)
            
            # Check for large price reductions
            if base_price > 0 and variant['price'] < base_price * 0.5:
                reduction = base_price - variant['price']
                reduction_percent = (reduction / base_price * 100)
                
                if 'margin_indicator' not in locals():  # Only add if we don't already have one
                    reduction_warning = QLabel(f"⚠️ -{reduction_percent:.0f}%")
                    reduction_warning.setStyleSheet("color: orange; font-size: 9px;")
                    price_layout.addWidget(reduction_warning)
                    
                if not price_spin.toolTip():
                    price_spin.setToolTip(f"Réduction excessive: {reduction_percent:.1f}% du prix de base")
            
            # Connect value changed after setting initial value
            price_spin.valueChanged.connect(lambda value, r=row: self.update_variant_price(r, value))
            
            price_layout.addWidget(price_spin)
            
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
            
            # Add warning icon for problematic variants
            if (purchase_price > 0 and variant['price'] < purchase_price) or not has_attributes:
                warning_btn = QPushButton("⚠️")
                warning_btn.setToolTip("Cette variante présente des problèmes (marge négative ou attributs manquants)")
                warning_btn.setFixedSize(30, 25)
                warning_btn.setStyleSheet("color: red; font-weight: bold;")
                actions_layout.addWidget(warning_btn)
            
            # Add buttons to actions layout
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            # Add to table
            self.variants_table.setCellWidget(row, 0, active_cell)
            self.variants_table.setItem(row, 1, name_item)
            self.variants_table.setItem(row, 2, sku_item)
            self.variants_table.setCellWidget(row, 3, price_widget)
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
