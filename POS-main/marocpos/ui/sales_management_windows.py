from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QHeaderView, QScrollArea, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCursor
from models.category import Category
from models.product import Product
from database import get_connection
from datetime import datetime
import pytz
import os

class ProductFrame(QFrame):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            ProductFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
            ProductFrame:hover {
                background-color: #f8f9fa;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        
        # Product image
        if self.product.get('image_path'):
            from PyQt5.QtGui import QPixmap
            import os
            
            image_path = self.product['image_path']
            if os.path.exists(image_path):
                image_label = QLabel()
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        100, 100,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(image_label)
        
        # Product name
        name_label = QLabel(self.product['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_label.setWordWrap(True)
        
        # Product price
        price_label = QLabel(f"{self.product['unit_price']:.2f} MAD")
        price_label.setAlignment(Qt.AlignCenter)
        price_label.setStyleSheet("color: #28a745; font-weight: bold;")
        
        # Stock info
        stock_label = QLabel(f"Stock: {self.product['stock']}")
        stock_label.setAlignment(Qt.AlignCenter)
        stock_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        
        # Has variants label
        if self.product.get('has_variants'):
            variant_label = QLabel("(Avec variantes)")
            variant_label.setAlignment(Qt.AlignCenter)
            variant_label.setStyleSheet("color: #0066cc; font-style: italic; font-size: 11px;")
            layout.addWidget(variant_label)
            
        layout.addWidget(name_label)
        layout.addWidget(price_label)
        layout.addWidget(stock_label)

class SalesManagementWindow(QWidget):
    def __init__(self, user=None):
        super().__init__()
        self.user_id = user['id'] if user else 1  # Default to user ID 1 if not provided
        self.current_datetime = datetime.now()
        self.current_amount = 0.0
        self.selected_row = None
        self.selected_product = None
        self.init_ui()
        self.setup_categories()
        self.load_products()

    def init_ui(self):
        self.setWindowTitle("Gestion des ventes")
        self.resize(1200, 800)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left section (cart and keypad)
        left_widget = self.create_left_section()
        main_layout.addWidget(left_widget)
        
        # Right section (categories and products)
        right_widget = self.create_right_section()
        main_layout.addWidget(right_widget, 2)  # Right section takes 2/3 of space

    def create_left_section(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Cart section
        cart_frame = QFrame()
        cart_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        cart_layout = QVBoxLayout(cart_frame)
        
        # Cart header
        cart_header = QLabel("Panier")
        cart_header.setStyleSheet("font-size: 18px; font-weight: bold;")
        cart_layout.addWidget(cart_header)
        
        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)  # Name, Quantity, Price, Remove
        self.cart_table.setHorizontalHeaderLabels(["Produit", "Quantité", "Prix", "Actions"])
        
        # Set column widths
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.cart_table.setColumnWidth(1, 70)
        self.cart_table.setColumnWidth(2, 70)
        self.cart_table.setColumnWidth(3, 50)
        
        self.cart_table.setStyleSheet("""
            QTableWidget {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #495057;
            }
            QTableWidget::item:selected {
                background-color: #e6f3ff;
                color: #000;
            }
        """)
        # Connect to item selection event
        self.cart_table.itemClicked.connect(self.on_cart_item_clicked)
        cart_layout.addWidget(self.cart_table)

        # Total section
        total_layout = QHBoxLayout()
        total_label = QLabel("Total à payer:")
        total_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.total_amount = QLabel("0.00 MAD")
        self.total_amount.setStyleSheet("font-weight: bold; font-size: 18px; color: #28a745;")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount, alignment=Qt.AlignRight)
        cart_layout.addLayout(total_layout)

        left_layout.addWidget(cart_frame)

        # Keypad section
        keypad_frame = self.create_keypad()
        left_layout.addWidget(keypad_frame)

        return left_widget

    def create_keypad(self):
        keypad_frame = QFrame()
        keypad_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        keypad_layout = QGridLayout(keypad_frame)
        keypad_layout.setSpacing(10)

        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('C', 0, 3),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('×', 1, 3),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('Annuler', 2, 3),
            ('0', 3, 0), ('.', 3, 1), ('00', 3, 2), ('Valider', 3, 3),
        ]

        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(80, 80)
            btn.setCursor(Qt.PointingHandCursor)
            
            if text == 'Valider':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
                btn.clicked.connect(self.process_sale)
            elif text == 'Annuler':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                btn.clicked.connect(self.clear_cart)
            elif text == 'C':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 18px;
                    }
                    QPushButton:hover {
                        background-color: #e0a800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #24786d;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 18px;
                    }
                    QPushButton:hover {
                        background-color: #1b5a52;
                    }
                """)
                btn.clicked.connect(lambda checked, t=text: self.keypad_pressed(t))
            
            keypad_layout.addWidget(btn, row, col)

        return keypad_frame

    def create_right_section(self):
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        # Categories section
        categories_scroll = QScrollArea()
        categories_scroll.setWidgetResizable(True)
        categories_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        categories_scroll.setMaximumHeight(150)

        categories_widget = QWidget()
        self.categories_layout = QGridLayout(categories_widget)
        self.categories_layout.setSpacing(10)
        categories_scroll.setWidget(categories_widget)
        
        self.setup_categories()
        right_layout.addWidget(categories_scroll)

        # Products section
        products_scroll = QScrollArea()
        products_scroll.setWidgetResizable(True)
        products_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        products_widget = QWidget()
        self.products_layout = QGridLayout(products_widget)
        self.products_layout.setSpacing(10)
        products_scroll.setWidget(products_widget)
        
        right_layout.addWidget(products_scroll)

        # Add receipt options
        receipt_layout = QHBoxLayout()
        receipt_layout.addWidget(QLabel("Reçu:"))
        
        self.receipt_options = QComboBox()
        self.receipt_options.addItems([
            "Imprimer (thermique)",
            "Imprimer (A4)",
            "Enregistrer en PDF",
            "Ne pas imprimer"
        ])
        receipt_layout.addWidget(self.receipt_options)
        
        receipt_settings_btn = QPushButton("⚙️")
        receipt_settings_btn.setToolTip("Paramètres du reçu")
        receipt_settings_btn.clicked.connect(self.open_receipt_settings)
        receipt_layout.addWidget(receipt_settings_btn)
        
        right_layout.addLayout(receipt_layout)

        return right_widget

    def on_cart_item_clicked(self, item):
        """Handle click on cart item"""
        self.selected_row = item.row()
        
        # If clicking on quantity column, select product for keypad
        if self.cart_table.currentColumn() == 1:
            self.selected_product = item.row()

    def keypad_pressed(self, text):
        """Handle keypad button press"""
        try:
            if self.selected_product is None:
                return
                
            # Get current quantity
            current_qty = self.cart_table.item(self.selected_row, 1).text()
            
            # Handle different keypad buttons
            if text == 'C':
                # Clear quantity
                current_qty = ""
            elif text == '×':
                # Remove last digit
                current_qty = current_qty[:-1] if current_qty else ""
                return
            else:
                # Add the text to the current quantity
                new_qty = current_qty + text
                
            # Try to convert to float and update if valid
            try:
                qty = float(new_qty) if new_qty else 1  # Default to 1 if empty
                if qty > 0:
                    self.cart_table.setItem(self.selected_row, 1, QTableWidgetItem(str(qty)))
                    self.update_total()
            except ValueError:
                # Invalid number, keep the current value
                pass
        except Exception as e:
            print(f"Error in keypad_pressed: {e}")

    def open_receipt_settings(self):
        """Open receipt settings dialog"""
        try:
            from .receipt_settings_dialog import ReceiptSettingsDialog
            dialog = ReceiptSettingsDialog(self)
            dialog.exec_()
        except Exception as e:
            print(f"Error opening receipt settings: {e}")
            QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir les paramètres du reçu: {str(e)}")
    
    def process_sale(self):
        """Process the sale and save to database"""
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, "Erreur", "Le panier est vide!")
            return

        try:
            # First show the payment dialog to collect payment information
            from .multi_payment_dialog import MultiPaymentDialog
            payment_dialog = MultiPaymentDialog(self.current_amount, self)
            
            if not payment_dialog.exec_():
                # User cancelled the payment dialog
                return
                
            # Get payment data from dialog
            payments_data = payment_dialog.get_payments_data()
            
            if not payments_data:
                QMessageBox.warning(self, "Erreur", "Aucun paiement n'a été enregistré.")
                return
                
            # Now process the sale with payment information
            conn = get_connection()
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Create sale record
                cursor.execute("""
                    INSERT INTO Sales (
                        created_at, 
                        total_amount, 
                        user_id,
                        discount,
                        tax_amount,
                        final_total,
                        payment_method,
                        payment_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    self.current_amount,
                    self.user_id,
                    0.0,  # discount (default to 0)
                    0.0,  # tax_amount (default to 0)
                    self.current_amount,  # final_total
                    "MULTIPLE" if len(payments_data) > 1 else payments_data[0]['method_name'],  # payment_method
                    "COMPLETED"  # payment_status
                ))
                
                sale_id = cursor.lastrowid
                
                # Add payment records
                from models.payment import Payment
                for payment in payments_data:
                    Payment.add_sale_payment(
                        sale_id=sale_id,
                        payment_method_id=payment['method_id'],
                        amount=payment['amount'],
                        reference_number=payment.get('reference', ''),
                        notes=payment.get('notes', '')
                    )
                
                # Add sale items
                for row in range(self.cart_table.rowCount()):
                    product_name = self.cart_table.item(row, 0).text()
                    quantity = float(self.cart_table.item(row, 1).text())
                    price = float(self.cart_table.item(row, 2).text())
                    
                    # Get product ID and variant ID from the item
                    product_id = self.cart_table.item(row, 0).data(Qt.UserRole)
                    variant_id = self.cart_table.item(row, 0).data(Qt.UserRole + 1)
                    
                    if not product_id:
                        # Fallback to old method if ID not stored in item
                        cursor.execute("SELECT id FROM Products WHERE name = ?", (product_name,))
                        product_id = cursor.fetchone()[0]
                    
                    # Calculate subtotal
                    subtotal = quantity * price
                    
                    # Add sale item
                    cursor.execute("""
                        INSERT INTO SaleItems (
                            sale_id,
                            product_id,
                            variant_id,
                            quantity,
                            unit_price,
                            subtotal
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (sale_id, product_id, variant_id, quantity, price, subtotal))
                    
                    # Update stock - different approach for variants vs regular products
                    if variant_id:
                        # Update variant stock
                        cursor.execute("""
                            UPDATE ProductVariants 
                            SET stock = stock - ? 
                            WHERE id = ?
                        """, (quantity, variant_id))
                    else:
                        # Update product stock
                        cursor.execute("""
                            UPDATE Products 
                            SET stock = stock - ? 
                            WHERE id = ?
                        """, (quantity, product_id))
                
                cursor.execute("COMMIT")
                
                # Show success message with payment details
                if len(payments_data) > 1:
                    payment_details = "\n".join([f"- {p['method_name']}: {p['amount']:.2f} MAD" for p in payments_data])
                    success_message = f"Vente #{sale_id} enregistrée avec succès!\n\nPaiements:\n{payment_details}"
                else:
                    success_message = f"Vente #{sale_id} enregistrée avec succès!\nPaiement par {payments_data[0]['method_name']}: {payments_data[0]['amount']:.2f} MAD"
                
                QMessageBox.information(self, "Succès", success_message)
                
                # Generate receipt based on selected option
                receipt_option = self.receipt_options.currentIndex()
                
                # Only generate receipt if not "Ne pas imprimer" (index 3)
                if receipt_option < 3:
                    try:
                        # Import the receipt generator
                        from .receipt_generator import ReceiptGenerator
                        
                        # Create receipt generator for this sale
                        receipt = ReceiptGenerator(sale_id, self)
                        
                        # Handle different receipt options
                        if receipt_option == 0:  # Thermal
                            receipt.print_thermal()
                        elif receipt_option == 1:  # A4
                            receipt.print_a4()
                        elif receipt_option == 2:  # PDF
                            receipt.generate_pdf()
                        else:
                            # Show the receipt preview dialog with all options
                            receipt.show_receipt_dialog()
                            
                    except Exception as e:
                        print(f"Error generating receipt: {e}")
                        QMessageBox.warning(
                            self, 
                            "Erreur d'impression", 
                            f"La vente a été enregistrée mais il y a eu une erreur lors de l'impression du reçu: {str(e)}"
                        )
                
                # Clear the cart
                self.clear_cart()
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                QMessageBox.warning(self, "Erreur", f"Erreur lors de l'enregistrement de la vente: {str(e)}")
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du traitement de la vente: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def remove_from_cart(self, row):
        """Remove an item from the cart"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            'Voulez-vous retirer cet article du panier ?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cart_table.removeRow(row)
            self.update_total()
            if row == getattr(self, 'selected_row', None):
                self.selected_product = None

    def update_total(self):
        """Update the total amount in the cart"""
        total = 0.0
        for row in range(self.cart_table.rowCount()):
            try:
                qty = float(self.cart_table.item(row, 1).text())
                price = float(self.cart_table.item(row, 2).text())
                total += qty * price
            except (ValueError, AttributeError):
                continue
        
        self.total_amount.setText(f"{total:.2f} MAD")
        self.current_amount = total

    def clear_cart(self):
        """Clear all items from the cart"""
        self.cart_table.setRowCount(0)
        self.update_total()
        self.selected_product = None
        self.selected_row = None

    def setup_categories(self):
        """Load categories into the UI"""
        categories = Category.get_all_categories()
        
        # Add special "All" category
        categories.insert(0, (None, "Tous les produits", None))
        
        # Clear existing widgets
        for i in reversed(range(self.categories_layout.count())):
            self.categories_layout.itemAt(i).widget().deleteLater()
        
        # Add categories to grid
        row = 0
        col = 0
        for category in categories:
            if col > 3:  # 4 categories per row
                col = 0
                row += 1
            
            btn = QPushButton(category[1])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    min-width: 150px;
                    min-height: 35px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            btn.clicked.connect(lambda checked, id=category[0]: self.filter_by_category(id))
            self.categories_layout.addWidget(btn, row, col)
            col += 1

    def load_products(self, category_id=None):
        # Clear existing products
        while self.products_layout.count():
            item = self.products_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get products
        products = Product.get_products_by_category(category_id)

        # Add products to grid
        row = 0
        col = 0
        for product in products:
            product_frame = ProductFrame(product)
            product_frame.mousePressEvent = lambda e, p=product: self.add_to_cart(p)
            
            self.products_layout.addWidget(product_frame, row, col)
            
            col += 1
            if col > 2:  # 3 products per row
                col = 0
                row += 1

    def filter_by_category(self, category_id):
        self.load_products(category_id)

    def add_to_cart(self, product):
        # Check if product has variants
        if product.get('has_variants'):
            try:
                # Import the variant selection dialog
                from .variant_selection_dialog import VariantSelectionDialog
                
                # Create and show the dialog
                dialog = VariantSelectionDialog(product, self)
                if dialog.exec_():
                    # Get the selected variant
                    variant = dialog.get_selected_variant()
                    if variant:
                        # Add the variant to the cart
                        self.add_variant_to_cart(product, variant)
                    else:
                        QMessageBox.warning(self, "Erreur", "Aucune variante sélectionnée.")
            except Exception as e:
                print(f"Error selecting variant: {e}")
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la sélection de la variante: {str(e)}")
            return
        
        # Regular product (no variants)
        # Check if product is already in cart
        for row in range(self.cart_table.rowCount()):
            product_id = self.cart_table.item(row, 0).data(Qt.UserRole)
            variant_id = self.cart_table.item(row, 0).data(Qt.UserRole + 1)
            
            # Match if same product and no variant
            if product_id == product['id'] and variant_id is None:
                # Update quantity
                current_qty = int(self.cart_table.item(row, 1).text())
                self.cart_table.setItem(row, 1, QTableWidgetItem(str(current_qty + 1)))
                self.update_total()
                return

        # Add new product to cart
        row = self.cart_table.rowCount()
        self.cart_table.insertRow(row)
        
        # Product name cell with product ID stored
        name_item = QTableWidgetItem(product['name'])
        name_item.setData(Qt.UserRole, product['id'])  # Store product ID
        name_item.setData(Qt.UserRole + 1, None)      # No variant
        self.cart_table.setItem(row, 0, name_item)
        
        # Quantity and price
        self.cart_table.setItem(row, 1, QTableWidgetItem("1"))
        self.cart_table.setItem(row, 2, QTableWidgetItem(f"{product['unit_price']:.2f}"))
        
        delete_btn = QPushButton("🗑")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #6c757d;
            }
            QPushButton:hover {
                color: #dc3545;
            }
        """)
        delete_btn.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
        
        btn_cell = QWidget()
        btn_layout = QHBoxLayout(btn_cell)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(delete_btn)
        
        self.cart_table.setCellWidget(row, 3, btn_cell)
        self.update_total()

    def add_variant_to_cart(self, product, variant):
        """Add a product variant to the cart"""
        try:
            # Check if the variant is already in the cart
            for row in range(self.cart_table.rowCount()):
                product_id = self.cart_table.item(row, 0).data(Qt.UserRole)
                variant_id = self.cart_table.item(row, 0).data(Qt.UserRole + 1)
                
                # Match if same product and same variant
                if product_id == product['id'] and variant_id == variant['id']:
                    # Update quantity
                    current_qty = int(self.cart_table.item(row, 1).text())
                    self.cart_table.setItem(row, 1, QTableWidgetItem(str(current_qty + 1)))
                    self.update_total()
                    return
            
            # Create variant name from product name + variant attributes
            attr_values = {}
            
            # Try both possible keys for attributes (for compatibility)
            for key in ['attributes', 'attribute_values']:
                if variant.get(key):
                    try:
                        # Handle different data structures
                        if isinstance(variant[key], str):
                            # Try to parse as JSON
                            try:
                                parsed_values = json.loads(variant[key])
                                attr_values = parsed_values
                                # Store the parsed result back in the variant for future use
                                variant[key] = parsed_values
                                # Also store in the other key for compatibility
                                other_key = 'attributes' if key == 'attribute_values' else 'attribute_values'
                                variant[other_key] = parsed_values
                            except json.JSONDecodeError:
                                # Not valid JSON, use as a simple string-value dictionary
                                attr_values = {key: variant[key]}
                        else:
                            attr_values = variant[key]
                            # Copy to other key for compatibility
                            other_key = 'attributes' if key == 'attribute_values' else 'attribute_values'
                            if other_key not in variant or not variant[other_key]:
                                variant[other_key] = attr_values
                    
                        # If we got values, no need to check the other key
                        if attr_values:
                            print(f"Successfully parsed {key}: {attr_values}")
                            break
                    except Exception as e:
                        print(f"Error parsing variant {key}: {e}")
                        
            # Debug output
            print(f"Variant in cart: {variant}")
            print(f"Extracted attribute values: {attr_values}")
            
            variant_desc = ""
            if attr_values:
                try:
                    # Handle different structures of attr_values
                    attr_vals = []
                    
                    # If attr_values is a dictionary with values
                    if isinstance(attr_values, dict):
                        attr_vals = [str(val) for val in attr_values.values() if val]
                    # If attr_values is a list
                    elif isinstance(attr_values, list):
                        attr_vals = [str(val) for val in attr_values if val]
                    # If it's some other structure, try to convert to string
                    else:
                        attr_vals = [str(attr_values)]
                    
                    # Join the values to create a description if we have values
                    if attr_vals:
                        variant_desc = " (" + " / ".join(attr_vals) + ")"
                except Exception as e:
                    print(f"Error creating variant description: {e}")
                    variant_desc = f" (Variante #{variant.get('id', '')})"
            
            variant_name = product['name'] + variant_desc
            
            # Calculate price - base price + adjustment
            base_price = float(product['unit_price'])
            price_adj = float(variant.get('price_adjustment', 0))
            final_price = base_price + price_adj
            
            # Add to cart
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            # Product name cell with product and variant IDs stored
            name_item = QTableWidgetItem(variant_name)
            name_item.setData(Qt.UserRole, product['id'])   # Store product ID
            name_item.setData(Qt.UserRole + 1, variant['id'])  # Store variant ID
            self.cart_table.setItem(row, 0, name_item)
            
            # Quantity and price
            self.cart_table.setItem(row, 1, QTableWidgetItem("1"))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{final_price:.2f}"))
            
            # Delete button
            delete_btn = QPushButton("🗑")
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    color: #6c757d;
                }
                QPushButton:hover {
                    color: #dc3545;
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
            
            btn_cell = QWidget()
            btn_layout = QHBoxLayout(btn_cell)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.addWidget(delete_btn)
            
            self.cart_table.setCellWidget(row, 3, btn_cell)
            self.update_total()
            
        except Exception as e:
            print(f"Error adding variant to cart: {e}")
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ajout de la variante au panier: {str(e)}")
