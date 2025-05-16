from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QListWidgetItem, QMessageBox, QGridLayout,
    QFrame, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from models.product import Product
import json
import os

class VariantSelectionDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.selected_variant = None
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
        
        # Variants list
        variants_label = QLabel("Choisissez une variante:")
        variants_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(variants_label)
        
        self.variants_list = QListWidget()
        self.variants_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: #000;
            }
        """)
        self.variants_list.itemDoubleClicked.connect(self.on_variant_double_clicked)
        main_layout.addWidget(self.variants_list)
        
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
        """Load product variants into the list"""
        variants = Product.get_variants(self.product['id'])
        
        if not variants:
            QMessageBox.warning(
                self,
                "Aucune variante",
                "Ce produit n'a pas de variantes configurées."
            )
            self.close()
            return
            
        for variant in variants:
            try:
                # Parse attribute values safely from either 'attributes' or 'attribute_values' key
                attr_values = {}
                
                # Try both possible keys for attributes (for compatibility with different data structures)
                for key in ['attributes', 'attribute_values']:
                    if variant.get(key):
                        try:
                            # Handle both string JSON and direct dictionary representation
                            if isinstance(variant[key], str):
                                parsed_values = json.loads(variant[key])
                                attr_values = parsed_values
                                # Add the parsed result back to the variant for later use
                                variant[key] = parsed_values
                            else:
                                attr_values = variant[key]
                            
                            # If we successfully parsed values, stop looking
                            if attr_values:
                                break
                        except Exception as e:
                            print(f"Error parsing {key}: {e}")
                
                # Debug output
                print(f"Variant {variant.get('id')}: Parsed attribute values: {attr_values}")
                
                # Create list item
                item = QListWidgetItem()
                
                # Create widget for the item
                item_widget = QFrame()
                item_layout = QHBoxLayout(item_widget)
                
                # Variant name/description
                variant_info = QVBoxLayout()
                
                # Create variant name from attributes
                variant_name = variant.get('name', '')
                if not variant_name and attr_values:
                    try:
                        # Ensure we have some kind of name even if we can't extract from attributes
                        default_name = f"Variante #{variant.get('id', '')}"
                    
                        # Try multiple approaches to get a meaningful name
                        attr_vals = []
                    
                        # First try: If we have a direct 'name' field, use it
                        if variant.get('name'):
                            variant_name = variant['name']
                        # Second try: Extract from attribute values dictionary
                        elif isinstance(attr_values, dict) and attr_values:
                            attr_vals = []
                            # Safely extract values from the dictionary
                            for attr_name, attr_value in attr_values.items():
                                if attr_value:
                                    # Handle if attr_value is another dict or a complex object
                                    if isinstance(attr_value, dict):
                                        # Try to extract a meaningful value from the dict
                                        for val in attr_value.values():
                                            if val:
                                                attr_vals.append(str(val))
                                                break
                                    else:
                                        attr_vals.append(str(attr_value))
                        
                            if attr_vals:
                                variant_name = " / ".join(attr_vals)
                            else:
                                variant_name = default_name
                        # Third try: If attr_values is a list
                        elif isinstance(attr_values, list) and attr_values:
                            attr_vals = [str(val) for val in attr_values if val]
                            if attr_vals:
                                variant_name = " / ".join(attr_vals)
                            else:
                                variant_name = default_name
                        # Fourth try: If attr_values is a string
                        elif isinstance(attr_values, str) and attr_values:
                            # Try to parse it as JSON, might be a serialized structure
                            try:
                                parsed = json.loads(attr_values)
                                if isinstance(parsed, dict):
                                    attr_vals = [str(val) for val in parsed.values() if val]
                                elif isinstance(parsed, list):
                                    attr_vals = [str(val) for val in parsed if val]
                                else:
                                    attr_vals = [str(parsed)]
                                
                                if attr_vals:
                                    variant_name = " / ".join(attr_vals)
                                else:
                                    variant_name = default_name
                            except:
                                # Not valid JSON, use as direct string
                                variant_name = attr_values
                        # Last resort: Use default name
                        else:
                            variant_name = default_name
                        
                        # Debug the name generation
                        print(f"Generated variant name: {variant_name} from attr_values: {attr_values}")
                        
                    except Exception as e:
                        print(f"Error creating variant name: {e}")
                        variant_name = f"Variante #{variant.get('id', '')}"
                    
                name_label = QLabel(variant_name)
                name_label.setStyleSheet("font-weight: bold;")
                variant_info.addWidget(name_label)
                
                # Add SKU if available
                if variant.get('sku'):
                    sku_label = QLabel(f"SKU: {variant['sku']}")
                    sku_label.setStyleSheet("font-size: 10px; color: #6c757d;")
                    variant_info.addWidget(sku_label)
                    
                # Add barcode if available
                if variant.get('barcode'):
                    barcode_label = QLabel(f"Code: {variant['barcode']}")
                    barcode_label.setStyleSheet("font-size: 10px; color: #6c757d;")
                    variant_info.addWidget(barcode_label)
                
                item_layout.addLayout(variant_info)
                
                # Price and stock
                price_stock = QVBoxLayout()
                price_stock.setAlignment(Qt.AlignRight)
                
                # Calculate adjusted price
                base_price = float(self.product['unit_price'])
                price_adj = float(variant.get('price_adjustment', 0))
                final_price = base_price + price_adj
                
                price_label = QLabel(f"{final_price:.2f} MAD")
                price_label.setStyleSheet("font-weight: bold; color: #28a745;")
                price_stock.addWidget(price_label)
                
                stock = int(variant.get('stock', 0))
                stock_color = "#dc3545" if stock <= 0 else "#28a745"
                stock_label = QLabel(f"Stock: {stock}")
                stock_label.setStyleSheet(f"color: {stock_color};")
                price_stock.addWidget(stock_label)
                
                item_layout.addLayout(price_stock)
                
                # Set item widget
                item.setSizeHint(item_widget.sizeHint())
                self.variants_list.addItem(item)
                self.variants_list.setItemWidget(item, item_widget)
                
                # Store variant data
                item.setData(Qt.UserRole, variant)
                
                # Disable item if no stock
                if stock <= 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    
            except Exception as e:
                print(f"Error loading variant: {e}")
                
        # Select first item if available and enabled
        if self.variants_list.count() > 0:
            for i in range(self.variants_list.count()):
                item = self.variants_list.item(i)
                if item.flags() & Qt.ItemIsEnabled:
                    self.variants_list.setCurrentItem(item)
                    break

    def on_variant_double_clicked(self, item):
        """Handle double click on a variant"""
        if item.flags() & Qt.ItemIsEnabled:
            self.accept_variant()

    def accept_variant(self):
        """Get selected variant and accept the dialog"""
        current_item = self.variants_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une variante.")
            return
            
        if not (current_item.flags() & Qt.ItemIsEnabled):
            QMessageBox.warning(self, "Stock insuffisant", "Cette variante n'est pas disponible.")
            return
            
        self.selected_variant = current_item.data(Qt.UserRole)
        self.accept()

    def get_selected_variant(self):
        """Return the selected variant"""
        return self.selected_variant
