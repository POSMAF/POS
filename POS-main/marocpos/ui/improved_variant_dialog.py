from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QListWidgetItem, QMessageBox, QGridLayout,
    QFrame, QDialogButtonBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import json
import os
import sys

# Import our variant manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from variant_manager import get_variant_attributes, get_variant_price_with_extras


class ImprovedVariantSelectionDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.variants = []
        self.selected_variant = None
        
        # Track selected attribute values
        self.selected_attributes = {}
        self.attribute_widgets = {}
        
        self.init_ui()
        self.load_variants()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Sélectionner une variante: {self.product['name']}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Product info header
        self.create_product_header(main_layout)
        
        # Attribute selection area
        attr_frame = QFrame()
        attr_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        self.attr_layout = QVBoxLayout(attr_frame)
        self.attr_layout.addWidget(QLabel("<b>Sélectionnez les attributs:</b>"))
        main_layout.addWidget(attr_frame)
        
        # Variant details area
        details_frame = QFrame()
        details_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        details_layout = QVBoxLayout(details_frame)
        
        details_layout.addWidget(QLabel("<b>Détails de la variante:</b>"))
        
        # SKU, barcode, stock
        self.sku_label = QLabel("SKU: -")
        self.barcode_label = QLabel("Code barre: -")
        self.stock_label = QLabel("Stock: -")
        
        details_layout.addWidget(self.sku_label)
        details_layout.addWidget(self.barcode_label)
        details_layout.addWidget(self.stock_label)
        
        # Price details
        price_frame = QFrame()
        price_frame.setStyleSheet("background-color: white; border-radius: 5px; padding: 10px;")
        price_layout = QVBoxLayout(price_frame)
        
        self.base_price_label = QLabel(f"Prix de base: {self.product['unit_price']:.2f} MAD")
        self.extras_label = QLabel("Suppléments: 0.00 MAD")
        self.total_price_label = QLabel(f"Prix final: {self.product['unit_price']:.2f} MAD")
        self.total_price_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #28a745;")
        
        price_layout.addWidget(self.base_price_label)
        price_layout.addWidget(self.extras_label)
        price_layout.addWidget(self.total_price_label)
        
        details_layout.addWidget(price_frame)
        main_layout.addWidget(details_frame)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_variant)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def create_product_header(self, layout):
        """Create the product information header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        # Product image if available
        if self.product.get('image_path') and os.path.exists(self.product['image_path']):
            image_label = QLabel()
            pixmap = QPixmap(self.product['image_path'])
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    80, 80,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                header_layout.addWidget(image_label)
                
        # Product info
        info_layout = QVBoxLayout()
        
        # Product name
        name_label = QLabel(self.product['name'])
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        # Base price
        price_label = QLabel(f"Prix de base: {self.product['unit_price']:.2f} MAD")
        price_label.setStyleSheet("color: #28a745;")
        info_layout.addWidget(price_label)
        
        # Get variant attributes
        variant_attrs = []
        if self.product.get('variant_attributes'):
            try:
                if isinstance(self.product['variant_attributes'], str):
                    variant_attrs = json.loads(self.product['variant_attributes'])
                else:
                    variant_attrs = self.product['variant_attributes']
            except:
                pass
                
        # Show attributes
        if variant_attrs:
            attrs_label = QLabel(f"Attributs: {', '.join(variant_attrs)}")
            attrs_label.setStyleSheet("color: #6c757d; font-style: italic;")
            info_layout.addWidget(attrs_label)
            
        header_layout.addLayout(info_layout)
        layout.addWidget(header_frame)
        layout.addSpacing(10)

    def load_variants(self):
        """Load product variants and organize by attributes"""
        from models.product import Product
        
        try:
            # Get variants
            self.variants = Product.get_variants(self.product['id'])
            
            if not self.variants:
                QMessageBox.warning(
                    self,
                    "Aucune variante",
                    "Ce produit n'a pas de variantes configurées."
                )
                self.close()
                return
            
            # Extract unique attributes and their values
            attributes = {}
            for variant in self.variants:
                # Get attributes for this variant
                variant_attrs = {}
                
                # Try to load from existing attribute values
                if variant.get('attributes') and isinstance(variant['attributes'], dict):
                    variant_attrs = variant['attributes']
                else:
                    # Get them from the database using the variant ID
                    variant_attrs = get_variant_attributes(variant['id'])
                
                print(f"Variant attributes for {variant['name']}: {variant_attrs}")
                
                # Store unique attributes and values
                for attr_name, attr_value in variant_attrs.items():
                    if attr_name not in attributes:
                        attributes[attr_name] = set()
                    attributes[attr_name].add(attr_value)
            
            # Create attribute selection widgets
            for attr_name, attr_values in attributes.items():
                # Create a combo box for each attribute
                attr_layout = QHBoxLayout()
                attr_layout.addWidget(QLabel(f"{attr_name}:"))
                
                attr_combo = QComboBox()
                attr_combo.addItem("", None)  # Empty selection
                
                # Add all values for this attribute
                for value in sorted(attr_values):
                    attr_combo.addItem(value, value)
                
                # Connect selection changed event
                attr_combo.currentIndexChanged.connect(self.on_attribute_changed)
                
                attr_layout.addWidget(attr_combo)
                self.attr_layout.addLayout(attr_layout)
                
                # Store the combo box widget
                self.attribute_widgets[attr_name] = attr_combo
        
        except Exception as e:
            print(f"Error loading variants: {e}")
            import traceback
            print(traceback.format_exc())
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des variantes: {e}")

    def on_attribute_changed(self):
        """Handle attribute selection change"""
        # Build the current selection
        self.selected_attributes = {}
        for attr_name, combo in self.attribute_widgets.items():
            if combo.currentData():
                self.selected_attributes[attr_name] = combo.currentData()
        
        print(f"Selected attributes: {self.selected_attributes}")
        
        # Find matching variant
        matching_variant = None
        for variant in self.variants:
            variant_attrs = {}
            
            # Try to load from existing attribute values
            if variant.get('attributes') and isinstance(variant['attributes'], dict):
                variant_attrs = variant['attributes']
            else:
                # Get them from the database using the variant ID
                variant_attrs = get_variant_attributes(variant['id'])
            
            # Check if all selected attributes match
            if self.selected_attributes and all(
                attr_name in variant_attrs and 
                variant_attrs[attr_name] == attr_value
                for attr_name, attr_value in self.selected_attributes.items()
            ):
                matching_variant = variant
                break
        
        # Update UI based on selected variant
        if matching_variant:
            self.selected_variant = matching_variant
            self.update_variant_details()
        else:
            self.selected_variant = None
            self.clear_variant_details()

    def update_variant_details(self):
        """Update the UI with selected variant details"""
        if not self.selected_variant:
            self.clear_variant_details()
            return
        
        # Update labels
        self.sku_label.setText(f"SKU: {self.selected_variant.get('sku', '-')}")
        self.barcode_label.setText(f"Code barre: {self.selected_variant.get('barcode', '-')}")
        
        stock = self.selected_variant.get('stock', 0)
        stock_color = "#dc3545" if stock <= 0 else "#28a745"
        self.stock_label.setText(f"Stock: {stock}")
        self.stock_label.setStyleSheet(f"color: {stock_color};")
        
        # Calculate and display price
        base_price = float(self.product['unit_price'])
        self.base_price_label.setText(f"Prix de base: {base_price:.2f} MAD")
        
        # Get price extras
        price_extras = 0
        if 'price_extras' in self.selected_variant:
            price_extras = float(self.selected_variant['price_extras'])
        elif 'total_price_adjustment' in self.selected_variant:
            price_extras = float(self.selected_variant['total_price_adjustment'])
        else:
            # Try to calculate it from database
            variant_price = get_variant_price_with_extras(self.selected_variant['id'])
            if variant_price:
                price_extras = variant_price - base_price
        
        self.extras_label.setText(f"Suppléments: {price_extras:.2f} MAD")
        
        # Calculate total price
        total_price = base_price + price_extras
        self.total_price_label.setText(f"Prix final: {total_price:.2f} MAD")

    def clear_variant_details(self):
        """Clear variant details when no selection"""
        self.sku_label.setText("SKU: -")
        self.barcode_label.setText("Code barre: -")
        self.stock_label.setText("Stock: -")
        self.stock_label.setStyleSheet("")
        
        # Reset price display
        base_price = float(self.product['unit_price'])
        self.base_price_label.setText(f"Prix de base: {base_price:.2f} MAD")
        self.extras_label.setText("Suppléments: 0.00 MAD")
        self.total_price_label.setText(f"Prix final: {base_price:.2f} MAD")

    def accept_variant(self):
        """Accept the selected variant"""
        if not self.selected_variant:
            QMessageBox.warning(
                self, 
                "Aucune sélection", 
                "Veuillez sélectionner une variante en choisissant les attributs."
            )
            return
        
        if self.selected_variant.get('stock', 0) <= 0:
            reply = QMessageBox.question(
                self,
                "Stock insuffisant",
                "Cette variante n'a pas de stock disponible. Voulez-vous continuer quand même?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        self.accept()

    def get_selected_variant(self):
        """Return the selected variant"""
        return self.selected_variant
