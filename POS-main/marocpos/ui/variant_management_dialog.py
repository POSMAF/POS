from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QWidget, QSplitter, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QDialogButtonBox, QDoubleSpinBox, QSpinBox,
    QFormLayout, QGroupBox, QTabWidget
)
from PyQt5.QtCore import Qt
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
        self.init_ui()
        self.load_attributes()

    def init_ui(self):
        self.setWindowTitle("Gestion des variantes de produit")
        self.setMinimumSize(900, 600)

        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_attributes_tab(), "1. Sélection des attributs")
        tabs.addTab(self.create_variants_tab(), "2. Variantes")
        
        main_layout.addWidget(tabs)
        
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
        self.variants_table.setColumnCount(6)
        self.variants_table.setHorizontalHeaderLabels([
            "Actif", "Variante", "SKU", "Prix de vente", "Stock", "Code-barres"
        ])
        
        self.variants_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.variants_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.variants_table.setColumnWidth(0, 50)
        
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
        
        layout.addLayout(bulk_layout)
        
        return tab

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
            
            # Add to table
            self.variants_table.setCellWidget(row, 0, active_cell)
            self.variants_table.setItem(row, 1, name_item)
            self.variants_table.setItem(row, 2, sku_item)
            self.variants_table.setCellWidget(row, 3, price_spin)
            self.variants_table.setCellWidget(row, 4, stock_spin)
            self.variants_table.setItem(row, 5, barcode_item)

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
