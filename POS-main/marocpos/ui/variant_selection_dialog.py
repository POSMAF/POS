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
                
                # Enhanced attribute extraction with more robust parsing
                # Try direct attributes dictionary first
                if variant.get('attributes') and isinstance(variant.get('attributes'), dict):
                    attr_values = variant.get('attributes')
                    print(f"Using attributes dict directly: {attr_values}")
                
                # Then try attribute_values dictionary
                elif variant.get('attribute_values') and isinstance(variant.get('attribute_values'), dict):
                    attr_values = variant.get('attribute_values')
                    print(f"Using attribute_values dict directly: {attr_values}")
                
                # Then try JSON strings
                else:
                    for key in ['attributes', 'attribute_values']:
                        if variant.get(key) and isinstance(variant[key], str):
                            try:
                                # Parse JSON with error handling
                                parsed_values = json.loads(variant[key])
                                
                                # Store both in attributes and attribute_values for consistency
                                variant['attributes'] = parsed_values
                                variant['attribute_values'] = parsed_values
                                attr_values = parsed_values
                                
                                print(f"Successfully parsed {key} JSON: {attr_values}")
                                break
                            except json.JSONDecodeError as e:
                                print(f"JSON parsing error for {key}: {e}")
                            except Exception as e:
                                print(f"General error parsing {key}: {e}")
                
                # Debug output with detailed info
                print(f"Variant {variant.get('id')}: Final parsed attribute values: {attr_values}")
                print(f"Variant data: {variant}")
                
                # Create list item
                item = QListWidgetItem()
                
                # Create widget for the item
                item_widget = QFrame()
                item_layout = QHBoxLayout(item_widget)
                
                # Variant name/description
                variant_info = QVBoxLayout()
                
                # Create variant name from attributes with improved handling
                # First use existing name if it exists and looks valid
                variant_name = variant.get('name', '')
                
                # If no name or we want to regenerate from attributes
                if (not variant_name or '/' not in variant_name) and attr_values:
                    try:
                        # Ensure we have some kind of name even if we can't extract from attributes
                        default_name = f"Variante #{variant.get('id', '')}"
                        
                        # Debug the incoming name and attributes
                        print(f"Generating name for variant {variant.get('id')}, existing name: '{variant_name}', attributes: {attr_values}")
                        
                        # Extract values from attribute_values with careful handling
                        attr_vals = []
                        
                        # If we have a direct 'name' field and it looks valid, use it
                        if variant.get('name') and '/' in variant.get('name'):
                            variant_name = variant['name']
                            print(f"Using existing name: {variant_name}")
                        
                        # Extract from attribute values dictionary (primary method)
                        elif isinstance(attr_values, dict) and attr_values:
                            attr_vals = []
                            
                            # Sort attributes by name for consistent display
                            for attr_name in sorted(attr_values.keys()):
                                attr_value = attr_values[attr_name]
                                
                                if attr_value:
                                    # Handle different types of attribute values
                                    if isinstance(attr_value, dict):
                                        # Extract from nested dictionary
                                        for val in attr_value.values():
                                            if val:
                                                attr_vals.append(str(val))
                                                print(f"Added nested value: {val}")
                                                break
                                    else:
                                        # Add simple attribute value
                                        attr_vals.append(str(attr_value))
                                        print(f"Added attribute: {attr_name}={attr_value}")
                            
                            # Create variant name from extracted values
                            if attr_vals:
                                variant_name = " / ".join(attr_vals)
                                print(f"Generated name from attributes: {variant_name}")
                            else:
                                variant_name = default_name
                                print(f"Using default name: {default_name}")
                        # Fallback to original variant name if it exists
                        elif variant.get('name'):
                            variant_name = variant['name']
                            print(f"Using existing name (fallback): {variant_name}")
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
                
                # Calculate adjusted price with all attribute price extras - enhanced version
                base_price = float(self.product['unit_price'])
                
                # Check if we have a unit_price directly on the variant (highest priority)
                if variant.get('unit_price') and float(variant.get('unit_price')) > 0:
                    final_price = float(variant.get('unit_price'))
                    print(f"Using direct variant price: {final_price}")
                else:
                    # Use total_price_adjustment which includes attribute price extras and variant price adjustment
                    if 'total_price_adjustment' in variant:
                        price_adj = float(variant.get('total_price_adjustment', 0))
                    else:
                        # Fallback to just the variant's price adjustment if the total isn't available
                        price_adj = float(variant.get('price_adjustment', 0))
                    
                    # Show detailed price breakdown for debugging
                    base_adj = float(variant.get('price_adjustment', 0))
                    attr_extras = variant.get('price_extras', 0)
                    
                    print(f"Variant {variant.get('id')} price calculation:")
                    print(f"  Base price: {base_price}")
                    print(f"  Variant adjustment: {base_adj}")
                    print(f"  Attribute extras: {attr_extras}")
                    print(f"  Total adjustment: {price_adj}")
                    
                    final_price = base_price + price_adj
                    print(f"  Final price: {final_price}")
                
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
