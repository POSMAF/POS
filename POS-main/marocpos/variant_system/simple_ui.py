"""
Simple UI for the Variant System

This module provides a simple UI for testing the variant system.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QDoubleSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt

from .attribute_manager import (
    AttributeType, AttributeValue, ProductAttribute, ProductAttributeValue,
    get_product_attributes_with_values
)
from .variant_manager import (
    ProductVariant, generate_variants_for_product, get_variant_with_attributes
)

class VariantSystemDialog(QDialog):
    """
    Dialog for managing product variants
    """
    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.product = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Système de Variantes")
        self.setMinimumSize(800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header with product info
        self.header_label = QLabel("Gestion des variantes pour le produit")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.header_label)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        # Attributes tab
        attributes_tab = QWidget()
        self.setup_attributes_tab(attributes_tab)
        tabs.addTab(attributes_tab, "Attributs")
        
        # Variants tab
        variants_tab = QWidget()
        self.setup_variants_tab(variants_tab)
        tabs.addTab(variants_tab, "Variantes")
        
        layout.addWidget(tabs)
        
        # Footer with buttons
        footer_layout = QHBoxLayout()
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        
        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
        
        # Load product data
        self.load_product_info()
    
    def setup_attributes_tab(self, tab):
        """Set up the attributes tab"""
        layout = QVBoxLayout(tab)
        
        # List of available attributes
        self.attributes_table = QTableWidget()
        self.attributes_table.setColumnCount(4)
        self.attributes_table.setHorizontalHeaderLabels([
            "Attribut", "Type d'affichage", "Obligatoire", "Affecte prix"
        ])
        self.attributes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.attributes_table)
        
        # Buttons for attribute management
        buttons_layout = QHBoxLayout()
        
        add_attr_btn = QPushButton("Ajouter un attribut")
        add_attr_btn.clicked.connect(self.add_attribute)
        
        buttons_layout.addWidget(add_attr_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
    
    def setup_variants_tab(self, tab):
        """Set up the variants tab"""
        layout = QVBoxLayout(tab)
        
        # List of variants
        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(5)
        self.variants_table.setHorizontalHeaderLabels([
            "Variante", "SKU", "Prix", "Stock", "Attributs"
        ])
        self.variants_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.variants_table)
        
        # Buttons for variant management
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Générer les variantes")
        generate_btn.clicked.connect(self.generate_variants)
        
        buttons_layout.addWidget(generate_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
    
    def load_product_info(self):
        """Load product information"""
        try:
            # This would normally come from your product model
            from models.product import Product
            
            product = Product.get_by_id(self.product_id)
            if product:
                self.product = product
                self.header_label.setText(f"Gestion des variantes pour: {product['name']}")
                
                # Load attributes and variants
                self.load_attributes()
                self.load_variants()
        except Exception as e:
            print(f"Error loading product info: {e}")
            self.product = {"id": self.product_id, "name": f"Product {self.product_id}"}
            self.header_label.setText(f"Gestion des variantes pour le produit {self.product_id}")
    
    def load_attributes(self):
        """Load product attributes"""
        try:
            # Get product attributes
            attributes = ProductAttribute.get_by_product(self.product_id)
            
            # Clear the table
            self.attributes_table.setRowCount(0)
            
            # Populate the table
            for i, attr in enumerate(attributes):
                self.attributes_table.insertRow(i)
                
                # Get attribute type
                attr_type = attr.attribute_type
                if not attr_type:
                    continue
                
                # Attribute name
                name_item = QTableWidgetItem(attr_type.display_name)
                self.attributes_table.setItem(i, 0, name_item)
                
                # Display type
                display_item = QTableWidgetItem(attr_type.display_type)
                self.attributes_table.setItem(i, 1, display_item)
                
                # Required
                required_item = QTableWidgetItem("✓" if attr.is_required else "")
                required_item.setTextAlignment(Qt.AlignCenter)
                self.attributes_table.setItem(i, 2, required_item)
                
                # Affects price
                price_item = QTableWidgetItem("✓" if attr.affects_price else "")
                price_item.setTextAlignment(Qt.AlignCenter)
                self.attributes_table.setItem(i, 3, price_item)
        except Exception as e:
            print(f"Error loading attributes: {e}")
    
    def load_variants(self):
        """Load product variants"""
        try:
            # Get product variants
            variants = ProductVariant.get_by_product(self.product_id)
            
            # Clear the table
            self.variants_table.setRowCount(0)
            
            # Populate the table
            for i, variant in enumerate(variants):
                self.variants_table.insertRow(i)
                
                # Get variant details
                variant_details = get_variant_with_attributes(variant.id)
                
                # Variant name
                name_item = QTableWidgetItem(variant.name)
                self.variants_table.setItem(i, 0, name_item)
                
                # SKU
                sku_item = QTableWidgetItem(variant.sku or "")
                self.variants_table.setItem(i, 1, sku_item)
                
                # Price
                price = variant.final_price or variant.base_price or 0
                price_item = QTableWidgetItem(f"{price:.2f}")
                self.variants_table.setItem(i, 2, price_item)
                
                # Stock
                stock = 0
                if variant_details and variant_details['inventory']:
                    stock = variant_details['inventory']['quantity']
                stock_item = QTableWidgetItem(str(stock))
                self.variants_table.setItem(i, 3, stock_item)
                
                # Attributes
                attrs = []
                if variant_details and variant_details['attributes']:
                    for attr_type_id, attr_data in variant_details['attributes'].items():
                        attrs.append(f"{attr_data['type_display_name']}: {attr_data['display_value']}")
                
                attrs_item = QTableWidgetItem(", ".join(attrs))
                self.variants_table.setItem(i, 4, attrs_item)
        except Exception as e:
            print(f"Error loading variants: {e}")
    
    def add_attribute(self):
        """Add an attribute to the product"""
        # Get all available attribute types
        attribute_types = AttributeType.get_all()
        
        if not attribute_types:
            QMessageBox.information(
                self,
                "Information",
                "Aucun attribut n'est défini dans le système. Veuillez en créer un d'abord."
            )
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un attribut")
        dialog.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout(dialog)
        
        # Form
        form_layout = QFormLayout()
        
        # Attribute type combo
        attr_combo = QComboBox()
        for attr_type in attribute_types:
            attr_combo.addItem(attr_type.display_name, attr_type.id)
        
        form_layout.addRow("Type d'attribut:", attr_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Get selected attribute type
            attr_type_id = attr_combo.currentData()
            
            # Create product attribute
            product_attr = ProductAttribute(
                product_id=self.product_id,
                attribute_type_id=attr_type_id,
                is_required=True,
                affects_price=True,
                affects_inventory=True
            )
            
            if product_attr.save():
                # Reload attributes
                self.load_attributes()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Succès",
                    "Attribut ajouté avec succès."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors de l'ajout de l'attribut."
                )
    
    def generate_variants(self):
        """Generate variants for the product"""
        # Check if the product has attributes
        attributes = ProductAttribute.get_by_product(self.product_id)
        
        if not attributes:
            QMessageBox.information(
                self,
                "Information",
                "Veuillez d'abord ajouter des attributs au produit."
            )
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Générer les variantes")
        dialog.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout(dialog)
        
        # Form
        form_layout = QFormLayout()
        
        # Base price
        base_price_spin = QDoubleSpinBox()
        base_price_spin.setRange(0, 99999)
        base_price_spin.setDecimals(2)
        base_price_spin.setValue(self.product.get('unit_price', 0) if self.product else 0)
        
        form_layout.addRow("Prix de base:", base_price_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Générer")
        generate_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(generate_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Get base price
            base_price = base_price_spin.value()
            
            # Generate variants
            variant_ids = generate_variants_for_product(self.product_id, base_price)
            
            if variant_ids:
                # Reload variants
                self.load_variants()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Succès",
                    f"{len(variant_ids)} variantes ont été générées avec succès."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors de la génération des variantes."
                )

# Function to show the dialog
def show_variant_dialog(product_id, parent=None):
    """Show the variant system dialog for a product"""
    dialog = VariantSystemDialog(product_id, parent)
    return dialog.exec_()
